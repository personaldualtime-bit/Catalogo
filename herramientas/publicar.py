#!/usr/bin/env python3
"""Convierte editar/productos.csv y editar/fotos/ en productos.js e img/, y lo sube a GitHub.

Antes copia el CSV y las fotos desde la carpeta compartida de la PC Windows (ORIGEN_*), si responde.

Lo ejecuta el timer de systemd cada minuto. Si no hubo cambios no hace nada.
Uso manual:  python3 herramientas/publicar.py [--sin-push] [--forzar]
"""
import csv
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import time
import unicodedata
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
EDITAR = RAIZ / "editar"
CSV = EDITAR / "productos.csv"
FOTOS = EDITAR / "fotos"
ESTADO = EDITAR / "ESTADO.txt"
IMG = RAIZ / "img"
SALIDA = RAIZ / "productos.js"
ORIGEN_RECURSO = "//central/Users"                              # carpeta compartida de la PC Windows
ORIGEN_CARPETA = "Public/Documents/CATALOGO-WEB-WSAPP/EDITAR"

ESPERA_SEG = 30          # no publica si algo se modificó hace menos de esto (edición en curso)
LADO_MAX = 800           # px del lado mayor de las fotos publicadas
EXT_FOTOS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"}
INACTIVO = {"no", "0", "false", "x", "agotado"}

avisos = []


def norm(s):
    s = unicodedata.normalize("NFD", str(s or ""))
    return "".join(c for c in s if unicodedata.category(c) != "Mn").lower()


def clave(s):
    return re.sub(r"[^a-z0-9]", "", norm(s))


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", norm(s)).strip("-")[:60]


def parsear_precio(v):
    """Acepta 12500, "12.500", "$ 12.500,50", "12,500.50"."""
    s = re.sub(r"[^\d.,]", "", str(v or ""))
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".") if s.rfind(",") > s.rfind(".") else s.replace(",", "")
    elif "," in s:
        s = s.replace(",", "") if re.search(r",\d{3}$", s) else s.replace(",", ".")
    elif re.search(r"\.\d{3}$", s):
        s = s.replace(".", "")
    try:
        n = float(s)
    except ValueError:
        return 0
    return int(n) if n.is_integer() else n


def leer_csv():
    """Lee el CSV tal como lo guarde Excel o LibreOffice: UTF-8 o ANSI, separado por ; o ,"""
    datos = CSV.read_bytes()
    try:
        texto = datos.decode("utf-8-sig")
    except UnicodeDecodeError:
        texto = datos.decode("cp1252")
    primera = texto.split("\n", 1)[0]
    sep = max([";", ",", "\t"], key=primera.count)
    filas = list(csv.reader(io.StringIO(texto), delimiter=sep))
    if filas and filas[0] and filas[0][0].lower().startswith("sep="):
        filas = filas[1:]
    if not filas:
        return []
    cols = [clave(c) for c in filas[0]]
    if "nombre" not in cols:
        raise ValueError(f"productos.csv no tiene columna 'nombre' (encabezados leídos: {filas[0]})")
    return [(n, dict(zip(cols, f))) for n, f in enumerate(filas[1:], start=2)]


# ---------- Carpeta de Windows ----------
def smb(*comandos):
    """Ejecuta comandos de smbclient dentro de la carpeta compartida de CENTRAL (sin contraseña)."""
    r = subprocess.run(["smbclient", "-N", "-t", "15", ORIGEN_RECURSO, "-D", ORIGEN_CARPETA, "-c", "; ".join(comandos)],
                       capture_output=True, text=True, timeout=120, env={"LC_ALL": "C", "PATH": "/usr/bin:/bin"})
    if r.returncode or "NT_STATUS" in r.stdout:
        raise OSError((r.stdout + r.stderr).strip().splitlines()[-1][:200])
    return r.stdout


def listar_smb(salida):
    """{nombre: (tamaño, mtime)} de las líneas de archivos de un 'ls' de smbclient."""
    archivos = {}
    for linea in salida.splitlines():
        m = re.match(r"^  (.+?)\s+([A-Z]*)\s+(\d+)\s+(\w{3} \w{3} [ \d]\d \d\d:\d\d:\d\d \d{4})$", linea)
        if m and "D" not in m.group(2) and m.group(1) not in (".", ".."):
            archivos[m.group(1)] = (int(m.group(3)), time.mktime(time.strptime(m.group(4), "%a %b %d %H:%M:%S %Y")))
    return archivos


def sincronizar():
    """Trae productos.csv y fotos/ desde CENTRAL a editar/. Si CENTRAL no responde usa la copia local."""
    try:
        raiz = listar_smb(smb("ls"))
        if "productos.csv" not in raiz:
            raise OSError("no está productos.csv en la carpeta EDITAR")
        fotos = {n: v for n, v in listar_smb(smb("ls fotos\\*")).items()
                 if Path(n).suffix.lower() in EXT_FOTOS and not n.startswith(("~", "."))}
        FOTOS.mkdir(parents=True, exist_ok=True)
        for otro, (_, t) in raiz.items():
            if otro != "productos.csv" and otro.lower().endswith((".csv", ".xlsx", ".xls")) \
                    and t > raiz["productos.csv"][1]:
                avisos.append(f"'{otro}' es más nuevo que productos.csv: si tiene cambios, "
                              "abrilo y guardalo como productos.csv (CSV)")
        pendientes = [("productos.csv", CSV, *raiz["productos.csv"])]
        pendientes += [(f"fotos\\{n}", FOTOS / n, *v) for n, v in fotos.items()]
        bajar = [(r, l, t) for r, l, tam, t in pendientes
                 if not l.exists() or l.stat().st_size != tam or int(l.stat().st_mtime) != int(t)]
        if bajar:
            smb(*[f'get "{r}" "{l}"' for r, l, _ in bajar])
            for _, local, t in bajar:
                os.utime(local, (t, t))
        for local in FOTOS.iterdir():
            if local.suffix.lower() in EXT_FOTOS and local.name not in fotos:
                local.unlink()
        return True
    except (OSError, subprocess.TimeoutExpired) as e:
        avisos.append(f"No se pudo leer la carpeta de CENTRAL ({e}); se usa la copia local")
        return False


# ---------- Fotos ----------
def procesar_fotos():
    """Genera img/<nombre>.jpg reducido por cada foto de editar/fotos. Devuelve {nombre-sin-ext: ruta publicada}."""
    IMG.mkdir(exist_ok=True)
    FOTOS.mkdir(parents=True, exist_ok=True)
    mapa, generados = {}, set()
    for src in sorted(FOTOS.iterdir()):
        if src.suffix.lower() not in EXT_FOTOS or src.name.startswith(("~", ".")):
            continue
        destino = IMG / (slug(src.stem) + ".jpg")
        if destino.name in generados:
            avisos.append(f"Foto repetida (mismo nombre con otra extensión): {src.name}")
            continue
        generados.add(destino.name)
        if not destino.exists() or destino.stat().st_mtime < src.stat().st_mtime:
            r = subprocess.run(
                ["convert", f"{src}[0]", "-auto-orient", "-background", "white", "-flatten",
                 "-resize", f"{LADO_MAX}x{LADO_MAX}>", "-strip", "-quality", "82", str(destino)],
                capture_output=True, text=True)
            if r.returncode:
                avisos.append(f"No se pudo convertir la foto {src.name}: {r.stderr.strip()[:200]}")
                destino.unlink(missing_ok=True)
                continue
        version = hashlib.md5(destino.read_bytes()).hexdigest()[:8]
        mapa[slug(src.stem)] = f"img/{destino.name}?v={version}"
    for viejo in IMG.glob("*.jpg"):
        if viejo.name not in generados:
            viejo.unlink()
    return mapa


def url_imagen(valor, id_, fotos):
    s = str(valor or "").strip()
    if not s:
        return fotos.get(slug(id_), "")
    m = re.search(r"drive\.google\.com/(?:file/d/|open\?id=|uc\?.*id=)([\w-]+)", s)
    if m:
        return f"https://drive.google.com/thumbnail?id={m.group(1)}&sz=w800"
    if re.match(r"https?://", s):
        return s
    ruta = fotos.get(slug(Path(s).stem))
    if not ruta:
        avisos.append(f"No existe la foto '{s}' en editar/fotos")
    return ruta or ""


# ---------- Productos ----------
def armar_productos(fotos):
    productos, vistos, usadas = [], {}, set()
    for fila, p in leer_csv():
        nombre = p.get("nombre", "").strip()
        imagen = p.get("imagen", "").strip()
        if not re.match(r"https?://", imagen):
            usadas.add(slug(Path(imagen).stem) if imagen else slug(p.get("id", "")))
        if not nombre:
            if any(v.strip() for v in p.values()):
                avisos.append(f"Fila {fila}: sin nombre, se ignora")
            continue
        if p.get("activo", "").strip().lower() in INACTIVO:
            continue
        categoria = p.get("categoria", "").strip() or "Otros"
        id_ = p.get("id", "").strip() or slug(f"{categoria} {nombre}")
        if id_ in vistos:
            avisos.append(f"Fila {fila}: código '{id_}' repetido (ya está en la fila {vistos[id_]}), se ignora")
            continue
        vistos[id_] = fila
        precio_txt = p.get("precio", "").strip()
        precio = parsear_precio(precio_txt)
        if precio_txt and not precio and not re.fullmatch(r"[$\s0.,]*|consultar", norm(precio_txt)):
            avisos.append(f"Fila {fila}: precio '{precio_txt}' no es un número, se muestra 'Consultar'")
        productos.append({
            "id": id_,
            "categoria": categoria,
            "marca": p.get("marca", "").strip(),
            "nombre": nombre,
            "precio": precio,
            "descripcion": p.get("descripcion", "").strip(),
            "imagen": url_imagen(p.get("imagen"), id_, fotos),
        })
    sueltas = sorted(set(fotos) - usadas)
    if sueltas:
        avisos.append("Fotos sin producto en productos.csv (agregá una fila con ese código): " + ", ".join(sueltas))
    return productos


# ---------- Git ----------
def git(*args, check=True):
    r = subprocess.run(["git", *args], cwd=RAIZ, capture_output=True, text=True)
    if check and r.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {(r.stderr or r.stdout).strip()}")
    return r.stdout.strip()


def subir():
    rutas = ["editar/productos.csv", "productos.js", "img"]
    git("add", "-A", "--", *rutas)
    if subprocess.run(["git", "diff", "--cached", "--quiet", "--", *rutas], cwd=RAIZ).returncode:
        git("commit", "-m", f"Actualizar catálogo ({datetime.now():%Y-%m-%d %H:%M})", "--", *rutas)
    if int(git("rev-list", "--count", "@{u}..HEAD") or 0):
        git("pull", "--rebase", "--autostash")
        git("push")
        return True
    return False


def ultima_modificacion():
    archivos = [CSV, *FOTOS.glob("*")] if FOTOS.exists() else [CSV]
    return max((f.stat().st_mtime for f in archivos if f.exists()), default=0)


def escribir_estado(resultado, en_windows=False):
    """Deja el resultado en ESTADO.txt (local y en la carpeta de Windows). Solo reescribe si cambió algo."""
    cuerpo = resultado + ("\r\n\r\nAvisos:\r\n" + "\r\n".join(f"  - {a}" for a in avisos) if avisos else "")
    try:
        anterior = ESTADO.read_text(encoding="utf-8-sig").split("  ", 1)[-1] if ESTADO.exists() else ""
        if cuerpo + "\r\n" != anterior or "subido" in resultado:
            ESTADO.write_text(f"{datetime.now():%d/%m/%Y %H:%M}  {cuerpo}\r\n", encoding="utf-8-sig")
            if en_windows:
                smb(f'put "{ESTADO}" ESTADO.txt')
    except (OSError, subprocess.TimeoutExpired):
        pass
    print(cuerpo.replace("\r\n", "\n"))


def main():
    sin_push = "--sin-push" in sys.argv
    en_windows = sincronizar()
    if "--forzar" not in sys.argv and time.time() - ultima_modificacion() < ESPERA_SEG:
        return  # todavía editando; se reintenta en la próxima pasada
    try:
        fotos = procesar_fotos()
        productos = armar_productos(fotos)
        nuevo = "window.CATALOGO = " + json.dumps({"productos": productos}, ensure_ascii=False, indent=1) + ";\n"
        if not SALIDA.exists() or SALIDA.read_text(encoding="utf-8") != nuevo:
            SALIDA.write_text(nuevo, encoding="utf-8")
        subido = False if sin_push else subir()
        resultado = f"OK — {len(productos)} productos publicados" + (" (subido a GitHub)" if subido else "")
    except Exception as e:  # noqa: BLE001 — cualquier error se informa en ESTADO.txt
        resultado = f"ERROR — {e}"
    escribir_estado(resultado, en_windows)
    if resultado.startswith("ERROR"):
        sys.exit(1)


if __name__ == "__main__":
    main()
