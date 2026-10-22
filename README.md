# Catálogo con carrito → WhatsApp

Sitio estático (HTML/CSS/JS, sin build) para GitHub Pages. El cliente arma un carrito y lo envía como mensaje de WhatsApp.

## Personalizar

Editá **`datos.js`**:
- `TIENDA.whatsapp`: tu número en formato internacional, solo dígitos (ej. `5491112345678`).
- `TIENDA.nombre`, `descripcion`, `moneda`, `locale`.
- `PRODUCTOS`: lista de productos. Las fotos van en `img/` y se referencian como `"img/archivo.jpg"`.

Para probar local, abrí `index.html` en el navegador (no necesita servidor).

## Publicar en GitHub Pages

```bash
git init
git add .
git commit -m "Catálogo inicial"
git branch -M main
git remote add origin https://github.com/USUARIO/catalogo.git
git push -u origin main
```

En GitHub: **Settings → Pages → Source: Deploy from a branch → `main` / `(root)`** → Save.
El sitio queda en `https://USUARIO.github.io/catalogo/`.
