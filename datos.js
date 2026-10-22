// ===========================================================
//  CONFIGURACIÓN DE LA TIENDA — editá solo este archivo
// ===========================================================

const TIENDA = {
  nombre: "Dual Time",
  descripcion: "Elegí tus productos y enviá el pedido por WhatsApp",
  // Número en formato internacional, solo dígitos (sin +, espacios ni guiones).
  // Ej. Argentina: 54 9 11 1234-5678 -> "5491112345678"
  whatsapp: "5492984501003",
  moneda: "ARS",
  locale: "es-AR",
};

// Planillas de Google Sheets publicadas como CSV (Archivo → Compartir → Publicar en la web → CSV).
// Podés poner una sola hoja con todo, o una URL por pestaña (Instrumentos, Audio, Iluminación…).
// Si una pestaña no tiene columna "categoria", se usa la "categoria" indicada acá.
// Mientras esta lista esté vacía, se muestran los PRODUCTOS de ejemplo de abajo.
const HOJAS = [
  // { url: "https://docs.google.com/spreadsheets/d/e/XXXX/pub?gid=0&single=true&output=csv" },
  // { url: "https://docs.google.com/spreadsheets/d/e/XXXX/pub?gid=123&single=true&output=csv", categoria: "Iluminación" },
];

// Productos de ejemplo (solo se usan si HOJAS está vacía).
const PRODUCTOS = [
  { id: "GUI-001", categoria: "Instrumentos", marca: "Yamaha", nombre: "Guitarra criolla C40", precio: 185000, imagen: "", descripcion: "Tapa de abeto, ideal para estudio." },
  { id: "TEC-001", categoria: "Instrumentos", marca: "Casio", nombre: "Teclado CT-S300", precio: 320000, imagen: "", descripcion: "61 teclas sensibles." },
  { id: "AUD-001", categoria: "Audio", marca: "JBL", nombre: "Parlante activo EON710", precio: 890000, imagen: "", descripcion: "10\", 1300 W." },
  { id: "AUD-002", categoria: "Audio", marca: "Behringer", nombre: "Consola Xenyx Q802USB", precio: 210000, imagen: "", descripcion: "8 canales con USB." },
  { id: "ILU-001", categoria: "Iluminación", marca: "", nombre: "Cabezal móvil LED 60 W", precio: 275000, imagen: "", descripcion: "DMX, 8 gobos." },
  { id: "ELE-001", categoria: "Electrónica", marca: "", nombre: "Cable XLR 6 m", precio: 15000, imagen: "", descripcion: "Conectores metálicos." },
];
