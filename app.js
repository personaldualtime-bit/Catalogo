(() => {
  const CLAVE_CARRITO = "carrito_" + TIENDA.whatsapp;
  const fmt = new Intl.NumberFormat(TIENDA.locale, { style: "currency", currency: TIENDA.moneda, maximumFractionDigits: 0 });
  const $ = (id) => document.getElementById(id);

  let carrito = cargarCarrito(); // { [id]: cantidad }
  let categoriaActiva = "Todas";
  let textoBusqueda = "";

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

  function buscarProducto(id) { return PRODUCTOS.find((p) => p.id === id); }

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
    const cats = ["Todas", ...new Set(PRODUCTOS.map((p) => p.categoria).filter(Boolean))];
    $("categorias").innerHTML = cats
      .map((c) => `<button class="chip ${c === categoriaActiva ? "activa" : ""}" data-cat="${escapar(c)}">${escapar(c)}</button>`)
      .join("");
  }

  function renderGrilla() {
    const q = textoBusqueda.toLowerCase();
    const lista = PRODUCTOS.filter((p) =>
      (categoriaActiva === "Todas" || p.categoria === categoriaActiva) &&
      (!q || p.nombre.toLowerCase().includes(q) || (p.descripcion || "").toLowerCase().includes(q))
    );
    $("vacio").hidden = lista.length > 0;
    $("grilla").innerHTML = lista.map((p) => `
      <article class="card">
        <img src="${escapar(p.imagen || placeholder(p.nombre))}" alt="${escapar(p.nombre)}" loading="lazy"
             onerror="this.onerror=null;this.src='${placeholder(p.nombre)}'">
        <div class="card-body">
          <h3>${escapar(p.nombre)}</h3>
          ${p.descripcion ? `<p class="desc muted">${escapar(p.descripcion)}</p>` : `<p class="desc"></p>`}
          <span class="precio">${fmt.format(p.precio)}</span>
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
          <strong>${fmt.format(i.precio * i.cant)}</strong>
          <span class="sub">${fmt.format(i.precio)} c/u</span>
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
      ...items().map((i) => `• ${i.cant} x ${i.nombre} — ${fmt.format(i.precio * i.cant)}`),
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
    renderCategorias();
    renderGrilla();
  });
  $("buscar").addEventListener("input", (e) => { textoBusqueda = e.target.value; renderGrilla(); });
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
  $("tienda-nombre").textContent = TIENDA.nombre;
  $("tienda-desc").textContent = TIENDA.descripcion;
  renderCategorias();
  renderGrilla();
  renderCarrito();
})();
