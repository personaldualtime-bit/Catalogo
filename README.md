# Catálogo con carrito → WhatsApp

Sitio estático (HTML/CSS/JS, sin build) para GitHub Pages. El cliente arma un carrito y lo envía como mensaje de WhatsApp.
Los productos se editan en una planilla local (`editar/productos.csv`); un script detecta los cambios y los publica solo.

```
editar/                 ← lo único que se toca (compartida en red para Windows)
├── productos.csv       lista de productos
├── fotos/              fotos originales (cualquier tamaño)
└── ESTADO.txt          resultado de la última publicación y avisos
productos.json, img/    los genera el script — no editar a mano
herramientas/           script de publicación e instaladores
```

## Uso diario

1. Abrí `editar/productos.csv` con Excel o LibreOffice, editá y **guardá como CSV** (si pregunta, "Mantener formato actual").
2. Copiá las fotos a `editar/fotos/`.
3. Listo: a los ~2 minutos se sube a GitHub, y GitHub Pages publica en ~1 minuto más.
   Si algo está mal (código repetido, foto inexistente, precio inválido) queda anotado en `editar/ESTADO.txt`.

- **Cargar:** agregá una fila.
- **Modificar:** editá la celda (precio, nombre…).
- **Ocultar** (sin stock, temporal): poné `no` en `activo`.
- **Borrar:** eliminá la fila.
- **Actualizar precios en masa:** pegá la lista nueva o usá una fórmula (ej. `=E2*1,1` para +10%) y guardá.

## Columnas de `productos.csv`

El orden no importa; mayúsculas y acentos tampoco. Se acepta separador `;` o `,`, en UTF-8 o ANSI (como guarde Excel).

| columna | obligatoria | ejemplo | notas |
|---|---|---|---|
| `nombre` | sí | Teclado CT-S300 | filas sin nombre se ignoran |
| `precio` | sí | 320000 / $ 320.000 | vacío, 0 o "consultar" → "Consultar" |
| `categoria` | recomendada | Audio | genera los filtros |
| `id` | recomendada | TEC-001 | código único; aparece en el pedido de WhatsApp |
| `marca` | no | Casio | se puede buscar |
| `descripcion` | no | 61 teclas sensibles | |
| `imagen` | no | vacío / `guitarra.jpg` / URL | ver abajo |
| `activo` | no | si / no | `no` oculta el producto sin borrarlo |

## Fotos

- **Lo más simple:** nombrá la foto con el código del producto (`TEC-001.jpg`) y dejá `imagen` vacía.
- Si la foto tiene otro nombre, escribilo en `imagen` (`teclado casio.png`).
- También sirve una URL pública o un link de Google Drive.
- Se publican reducidas a 800 px en `img/`. Los originales en `editar/fotos/` no se suben a GitHub.

## Instalación (una sola vez, en la PC Linux)

```bash
bash herramientas/instalar-timer.sh          # publicación automática cada minuto
sudo bash herramientas/instalar-samba.sh     # compartir editar/ en la red
```

Comandos útiles:

```bash
python3 herramientas/publicar.py --forzar    # publicar ya, sin esperar
journalctl --user -u catalogo-publicar -n 20 # ver lo que hizo el timer
systemctl --user disable --now catalogo-publicar.timer   # pausar publicación automática
```

El timer corre mientras la sesión del usuario está abierta. Para que corra aunque nadie haya iniciado sesión: `sudo loginctl enable-linger $USER`.

## Editar desde Windows 7 (misma red)

1. **Equipo → Conectar a unidad de red**, carpeta `\\DT-FM\catalogo` (o `\\<IP de la PC Linux>\catalogo`).
2. Marcá "Conectar con otras credenciales": usuario `dt-fiske` y la contraseña elegida al instalar Samba.
3. Abrí `productos.csv` desde esa unidad y guardá normalmente.

Conviene reservar la IP de la PC Linux en el router para que la dirección no cambie.

## Publicar cambios de código / configuración

`datos.js` tiene nombre, WhatsApp y moneda de la tienda.

```bash
git commit -am "descripción del cambio" && git push
```
GitHub Pages: Settings → Pages → Deploy from a branch → `main` / `(root)`.
