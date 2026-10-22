# Catálogo con carrito → WhatsApp

Sitio estático (HTML/CSS/JS, sin build) para GitHub Pages. El cliente arma un carrito y lo envía como mensaje de WhatsApp.
Los productos se administran desde **Google Sheets**: lo que cambies en la planilla aparece en el sitio sin tocar código.

## 1. Crear la planilla (una sola vez)

1. Creá una planilla en Google Sheets e importá `plantilla.csv` (Archivo → Importar).
2. Columnas (el orden no importa, mayúsculas y acentos tampoco):

| columna | obligatoria | ejemplo | notas |
|---|---|---|---|
| `nombre` | sí | Teclado CT-S300 | |
| `precio` | sí | 320000 / $ 320.000 | vacío o 0 → "Consultar" |
| `categoria` | recomendada | Audio | genera los filtros |
| `id` | recomendada | TEC-001 | código único; aparece en el pedido de WhatsApp |
| `marca` | no | Casio | se puede buscar |
| `descripcion` | no | 61 teclas sensibles | |
| `imagen` | no | link de Drive o URL | ver abajo |
| `activo` | no | si / no | `no` oculta el producto sin borrarlo |

3. **Archivo → Compartir → Publicar en la web** → elegí la hoja → formato **CSV** → Publicar. Copiá la URL.
4. Pegala en `datos.js` dentro de `HOJAS` y subí el cambio a GitHub (única vez).

Podés usar **una pestaña por rubro** (Instrumentos, Audio, Iluminación…): publicá cada una y agregá una línea por pestaña en `HOJAS`.
Si la pestaña no tiene columna `categoria`, se usa la indicada en `HOJAS`.

## 2. Uso diario

- **Cargar:** agregá una fila.
- **Modificar:** editá la celda (precio, nombre, foto…).
- **Ocultar** (sin stock, temporal): poné `no` en `activo`.
- **Borrar:** eliminá la fila.
- **Actualizar precios en masa:** pegá la lista nueva o usá una fórmula (ej. `=B2*1.1` para +10%).

Los cambios aparecen en el sitio en ~5 minutos (demora de caché de Google).

## Imágenes

- **Google Drive:** subí la foto, Compartir → "Cualquier persona con el enlace", y pegá ese link en `imagen`. Se convierte solo.
- **Otra URL pública** (la web del fabricante, Imgur, etc.) también sirve.
- Sin imagen se muestra la inicial del producto.

## Publicar cambios de código / configuración

```bash
git commit -am "descripción del cambio" && git push
```
GitHub Pages: Settings → Pages → Deploy from a branch → `main` / `(root)`.
