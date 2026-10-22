// ===========================================================
//  CONFIGURACIÓN DE LA TIENDA — editá solo este archivo
// ===========================================================

const TIENDA = {
  nombre: "Mi Tienda",
  descripcion: "Elegí tus productos y enviá el pedido por WhatsApp",
  // Número en formato internacional, solo dígitos (sin +, espacios ni guiones).
  // Ej. Argentina: 54 9 11 1234-5678 -> "5491112345678"
  whatsapp: "5491112345678",
  moneda: "ARS",
  locale: "es-AR",
};

// Cada producto: id único, nombre, precio, categoría, imagen (opcional) y descripción (opcional).
// Las imágenes van en la carpeta img/ (ej. "img/remera.jpg"). Si no hay imagen, se muestra un placeholder.
const PRODUCTOS = [
  { id: "p1", nombre: "Remera básica", precio: 12000, categoria: "Ropa", imagen: "", descripcion: "Algodón 100%, varios colores." },
  { id: "p2", nombre: "Buzo con capucha", precio: 28500, categoria: "Ropa", imagen: "", descripcion: "Frisa invierno." },
  { id: "p3", nombre: "Gorra", precio: 9000, categoria: "Accesorios", imagen: "", descripcion: "Talle único, regulable." },
  { id: "p4", nombre: "Taza cerámica", precio: 7500, categoria: "Hogar", imagen: "", descripcion: "350 ml, apta microondas." },
  { id: "p5", nombre: "Tote bag", precio: 8000, categoria: "Accesorios", imagen: "", descripcion: "Lienzo resistente." },
  { id: "p6", nombre: "Vela aromática", precio: 6500, categoria: "Hogar", imagen: "", descripcion: "Cera de soja, 40 h." },
];
