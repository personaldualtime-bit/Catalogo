(() => {
  const CLAVE_CARRITO = "carrito_" + TIENDA.whatsapp;
  const POR_PAGINA = 48;
  const fmt = new Intl.NumberFormat(TIENDA.locale, { style: "currency", currency: TIENDA.moneda, maximumFractionDigits: 0 });
  const $ = (id) => document.getElementById(id);

  let productos = [];
  let carrito = {}; // { [id]: cantidad }
  let categoriaActiva = "Todas";
  let textoBusqueda = "";
  let visibles = POR_PAGINA;

  // ---------- Carga de datos ----------
  // productos.json lo genera herramientas/publicar.py a partir de editar/productos.csv
  async function cargarProductos() {
    const resp = await fetch("productos.json", { cache: "no-cache" });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return (await resp.json()).productos;
  }

  function norm(s) {
    return String(s ?? "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
  }

  // ---------- Persistencia ----------
  function cargarCarrito() {
    try {
      const guardado = JSON.parse(localStorage.getItem(CLAVE_CARRITO)) || {};
      // Descarta productos que ya no existen en el catálogo
      return Object.fromEntries(Object.entries(guardado).filter(([id]) => buscarProducto(id)));
    } catch { return {}; }
  }
  function guardarCarrito() {
    try { localStorage.setItem(CLAVE_CARRITO, JSON.stringify(carrito)); } catch {}
  }

  function buscarProducto(id) { return productos.find((p) => p.id === id); }

  function placeholder(nombre) {
    const letra = (nombre || "?").trim().charAt(0).toUpperCase();
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect width="100" height="100" fill="#d9d9d4"/><text x="50" y="62" font-size="40" text-anchor="middle" fill="#8a8a85" font-family="sans-serif">${letra}</text></svg>`;
    return "data:image/svg+xml," + encodeURIComponent(svg);
  }

  function escapar(s) {
    return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }

  // ---------- Catálogo ----------
  function renderCategorias() {
    const cats = ["Todas", ...new Set(productos.map((p) => p.categoria))];
    $("categorias").innerHTML = cats
      .map((c) => `<button class="chip ${c === categoriaActiva ? "activa" : ""}" data-cat="${escapar(c)}">${escapar(c)}</button>`)
      .join("");
  }

  function filtrados() {
    const palabras = norm(textoBusqueda).split(/\s+/).filter(Boolean);
    return productos.filter((p) => {
      if (categoriaActiva !== "Todas" && p.categoria !== categoriaActiva) return false;
      const texto = norm(`${p.nombre} ${p.marca} ${p.descripcion} ${p.id}`);
      return palabras.every((w) => texto.includes(w));
    });
  }

  function renderGrilla() {
    const lista = filtrados();
    $("vacio").hidden = lista.length > 0;
    $("ver-mas").hidden = lista.length <= visibles;
    $("grilla").innerHTML = lista.slice(0, visibles).map((p) => `
      <article class="card">
        <img src="${escapar(p.imagen || placeholder(p.nombre))}" alt="${escapar(p.nombre)}" loading="lazy"
             onerror="this.onerror=null;this.src='${placeholder(p.nombre)}'">
        <div class="card-body">
          ${p.marca ? `<span class="marca">${escapar(p.marca)}</span>` : ""}
          <h3>${escapar(p.nombre)}</h3>
          ${p.descripcion ? `<p class="desc muted">${escapar(p.descripcion)}</p>` : `<p class="desc"></p>`}
          <span class="precio">${p.precio ? fmt.format(p.precio) : "Consultar"}</span>
          <button class="add-btn" data-add="${escapar(p.id)}">Agregar</button>
        </div>
      </article>`).join("");
  }

  // ---------- Carrito ----------
  function cambiarCantidad(id, delta) {
    const nueva = (carrito[id] || 0) + delta;
    if (nueva <= 0) delete carrito[id];
    else carrito[id] = nueva;
    guardarCarrito();
    renderCarrito();
  }

  function items() {
    return Object.entries(carrito).map(([id, cant]) => ({ ...buscarProducto(id), cant }));
  }
  function total() { return items().reduce((s, i) => s + i.precio * i.cant, 0); }
  function precioTexto(i) { return i.precio ? fmt.format(i.precio * i.cant) : "a consultar"; }

  function renderCarrito() {
    const lista = items();
    const unidades = lista.reduce((s, i) => s + i.cant, 0);
    $("cart-count").textContent = unidades;
    $("cart-total").textContent = fmt.format(total());
    $("enviar").disabled = lista.length === 0;
    $("cart-items").innerHTML = lista.length
      ? lista.map((i) => `
        <div class="cart-item">
          <span class="nombre">${escapar(i.nombre)}</span>
          <strong>${precioTexto(i)}</strong>
          <span class="sub">${i.precio ? `${fmt.format(i.precio)} c/u` : ""}</span>
          <div class="qty">
            <button data-menos="${escapar(i.id)}" aria-label="Quitar uno">−</button>
            <span>${i.cant}</span>
            <button data-mas="${escapar(i.id)}" aria-label="Agregar uno">+</button>
          </div>
        </div>`).join("")
      : `<p class="muted center">Tu carrito está vacío.</p>`;
  }

  function abrirCarrito(abrir) {
    $("carrito").classList.toggle("abierto", abrir);
    $("carrito").setAttribute("aria-hidden", String(!abrir));
    $("overlay").hidden = !abrir;
  }

  // ---------- WhatsApp ----------
  function armarMensaje() {
    const nombre = $("cliente-nombre").value.trim();
    const nota = $("cliente-nota").value.trim();
    const lineas = [
      `Hola ${TIENDA.nombre}! Quiero hacer este pedido:`,
      "",
      ...items().map((i) => `• ${i.cant} x ${i.marca ? i.marca + " " : ""}${i.nombre} [${i.id}] — ${precioTexto(i)}`),
      "",
      `*Total: ${fmt.format(total())}*`,
    ];
    if (nombre) lineas.push("", `Nombre: ${nombre}`);
    if (nota) lineas.push(`Notas: ${nota}`);
    return lineas.join("\n");
  }

  function enviarPedido() {
    if (!items().length) return;
    const url = `https://wa.me/${TIENDA.whatsapp}?text=${encodeURIComponent(armarMensaje())}`;
    window.open(url, "_blank", "noopener");
  }

  let toastTimer;
  function toast(msg) {
    let el = document.querySelector(".toast");
    if (!el) { el = document.createElement("div"); el.className = "toast"; document.body.appendChild(el); }
    el.textContent = msg;
    el.classList.add("visible");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => el.classList.remove("visible"), 1500);
  }

  // ---------- Eventos ----------
  $("categorias").addEventListener("click", (e) => {
    const cat = e.target.dataset.cat;
    if (!cat) return;
    categoriaActiva = cat;
    visibles = POR_PAGINA;
    renderCategorias();
    renderGrilla();
  });
  $("buscar").addEventListener("input", (e) => { textoBusqueda = e.target.value; visibles = POR_PAGINA; renderGrilla(); });
  $("ver-mas").addEventListener("click", () => { visibles += POR_PAGINA; renderGrilla(); });
  $("grilla").addEventListener("click", (e) => {
    const id = e.target.dataset.add;
    if (!id) return;
    cambiarCantidad(id, 1);
    toast(`${buscarProducto(id).nombre} agregado`);
  });
  $("cart-items").addEventListener("click", (e) => {
    if (e.target.dataset.mas) cambiarCantidad(e.target.dataset.mas, 1);
    if (e.target.dataset.menos) cambiarCantidad(e.target.dataset.menos, -1);
  });
  $("abrir-carrito").addEventListener("click", () => abrirCarrito(true));
  $("cerrar-carrito").addEventListener("click", () => abrirCarrito(false));
  $("overlay").addEventListener("click", () => abrirCarrito(false));
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") abrirCarrito(false); });
  $("enviar").addEventListener("click", enviarPedido);
  $("vaciar").addEventListener("click", () => {
    if (!items().length || !confirm("¿Vaciar el carrito?")) return;
    carrito = {};
    guardarCarrito();
    renderCarrito();
  });

  // ---------- Init ----------
  document.title = TIENDA.nombre;
  $("tienda-logo").alt = TIENDA.nombre;
  $("tienda-desc").textContent = TIENDA.descripcion;
  renderCarrito();

  cargarProductos()
    .then((lista) => {
      productos = lista;
      carrito = cargarCarrito();
      $("cargando").hidden = true;
      renderCategorias();
      renderGrilla();
      renderCarrito();
    })
    .catch((err) => {
      console.error(err);
      $("cargando").textContent = "No se pudo cargar el catálogo. Probá recargar la página.";
    });
})();
