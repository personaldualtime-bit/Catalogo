#!/usr/bin/env python3
"""Convierte editar/productos.csv y editar/fotos/ en productos.json e img/, y lo sube a GitHub.

Lo ejecuta el timer de systemd cada minuto. Si no hubo cambios no hace nada.
Uso manual:  python3 herramientas/publicar.py [--sin-push] [--forzar]
"""
import csv
import hashlib
import io
import json
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
JSON = RAIZ / "productos.json"

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
    productos, vistos = [], {}
    for fila, p in leer_csv():
        nombre = p.get("nombre", "").strip()
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
    return productos


# ---------- Git ----------
def git(*args, check=True):
    r = subprocess.run(["git", *args], cwd=RAIZ, capture_output=True, text=True)
    if check and r.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {(r.stderr or r.stdout).strip()}")
    return r.stdout.strip()


def subir():
    rutas = ["editar/productos.csv", "productos.json", "img"]
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


def escribir_estado(resultado):
    """Deja el resultado en editar/ESTADO.txt (visible desde Windows). Solo reescribe si cambió algo."""
    cuerpo = resultado + ("\r\n\r\nAvisos:\r\n" + "\r\n".join(f"  - {a}" for a in avisos) if avisos else "")
    try:
        anterior = ESTADO.read_text(encoding="utf-8-sig").split("  ", 1)[-1] if ESTADO.exists() else ""
        if cuerpo + "\r\n" != anterior or "subido" in resultado:
            ESTADO.write_text(f"{datetime.now():%d/%m/%Y %H:%M}  {cuerpo}\r\n", encoding="utf-8-sig")
    except OSError:
        pass
    print(cuerpo.replace("\r\n", "\n"))


def main():
    sin_push = "--sin-push" in sys.argv
    if "--forzar" not in sys.argv and time.time() - ultima_modificacion() < ESPERA_SEG:
        return  # todavía editando; se reintenta en la próxima pasada
    try:
        fotos = procesar_fotos()
        productos = armar_productos(fotos)
        nuevo = json.dumps({"productos": productos}, ensure_ascii=False, indent=1) + "\n"
        if not JSON.exists() or JSON.read_text(encoding="utf-8") != nuevo:
            JSON.write_text(nuevo, encoding="utf-8")
        subido = False if sin_push else subir()
        resultado = f"OK — {len(productos)} productos publicados" + (" (subido a GitHub)" if subido else "")
    except Exception as e:  # noqa: BLE001 — cualquier error se informa en ESTADO.txt
        resultado = f"ERROR — {e}"
    escribir_estado(resultado)
    if resultado.startswith("ERROR"):
        sys.exit(1)


if __name__ == "__main__":
    main()
