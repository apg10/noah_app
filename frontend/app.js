(function () {
  "use strict";

  const KEY = {
    api: "noah_api_base_url",
    token: "noah_auth_token",
    cart: "noah_cart_v1",
    restaurant: "noah_restaurant_id",
    lastOrder: "noah_last_order_id",
    lastItem: "noah_last_menu_item_id"
  };

  const PAGE = (window.location.pathname.split("/").pop() || "index.html").toLowerCase();

  function pInt(v) {
    const n = Number.parseInt(String(v || ""), 10);
    return Number.isNaN(n) ? null : n;
  }

  function esc(v) {
    return String(v || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function cop(v) {
    return new Intl.NumberFormat("es-CO", {
      style: "currency",
      currency: "COP",
      maximumFractionDigits: 0
    }).format(Number(v || 0));
  }

  function arr(data) {
    if (Array.isArray(data)) return data;
    if (data && Array.isArray(data.results)) return data.results;
    return [];
  }

  function apiBase() {
    const fromStorage = (localStorage.getItem(KEY.api) || "").trim();
    if (fromStorage) return fromStorage.replace(/\/+$/, "");
    if (location.protocol.startsWith("http")) return `${location.origin}/api`;
    return "http://127.0.0.1:8000/api";
  }

  function authHeader() {
    const raw = (localStorage.getItem(KEY.token) || "").trim();
    if (!raw) return "";
    if (raw.startsWith("Token ") || raw.startsWith("Bearer ") || raw.startsWith("Basic ")) return raw;
    return `Token ${raw}`;
  }

  function saveAuthToken(token) {
    const raw = String(token || "").trim();
    if (!raw) {
      localStorage.removeItem(KEY.token);
      return;
    }
    if (raw.startsWith("Token ") || raw.startsWith("Bearer ") || raw.startsWith("Basic ")) {
      localStorage.setItem(KEY.token, raw);
      return;
    }
    localStorage.setItem(KEY.token, `Token ${raw}`);
  }

  function errMsg(data) {
    if (!data) return "";
    if (typeof data === "string") return data;
    if (data.detail) return String(data.detail);
    const k = Object.keys(data)[0];
    if (!k) return "";
    const v = data[k];
    if (Array.isArray(v)) return `${k}: ${v.join(", ")}`;
    return typeof v === "string" ? `${k}: ${v}` : JSON.stringify(data);
  }

  async function req(path, opts) {
    const headers = { Accept: "application/json", ...(opts?.headers || {}) };
    const token = authHeader();
    if (token) headers.Authorization = token;

    let body = opts?.body;
    if (body && typeof body !== "string") {
      headers["Content-Type"] = "application/json";
      body = JSON.stringify(body);
    }

    const res = await fetch(`${apiBase()}${path}`, {
      method: opts?.method || "GET",
      headers,
      body,
      credentials: "include"
    });

    const text = await res.text();
    let data = null;
    if (text) {
      try {
        data = JSON.parse(text);
      } catch {
        data = text;
      }
    }

    if (!res.ok) {
      const e = new Error(errMsg(data) || `HTTP ${res.status}`);
      e.status = res.status;
      throw e;
    }

    return data;
  }

  const api = {
    listCategories: async () => arr(await req("/categories/")),
    listMenuItems: async () => arr(await req("/menu-items/")),
    getMenuItem: async (id) => req(`/menu-items/${id}/`),
    createOrder: async (payload) => req("/orders/", { method: "POST", body: payload }),
    listOrders: async () => arr(await req("/orders/")),
    getOrder: async (id) => req(`/orders/${id}/`),
    login: async (username, password) => req("/auth/login/", { method: "POST", body: { username, password } }),
    me: async () => req("/auth/me/"),
    logout: async () => req("/auth/logout/", { method: "POST", body: {} })
  };

  function readCart() {
    try {
      const c = JSON.parse(localStorage.getItem(KEY.cart) || "{}");
      if (!Array.isArray(c.items)) c.items = [];
      return {
        restaurant_id: pInt(c.restaurant_id),
        items: c.items
          .map((i) => ({
            id: pInt(i.id),
            name: String(i.name || "Producto"),
            price_cop: Number(i.price_cop || 0),
            image_url: String(i.image_url || ""),
            quantity: Math.max(1, pInt(i.quantity) || 1),
            restaurant: pInt(i.restaurant),
            category: pInt(i.category)
          }))
          .filter((i) => i.id)
      };
    } catch {
      return { restaurant_id: null, items: [] };
    }
  }

  function saveCart(cart) {
    localStorage.setItem(KEY.cart, JSON.stringify(cart));
    return cart;
  }

  function addCart(item, qty) {
    const cart = readCart();
    const q = Math.max(1, pInt(qty) || 1);
    const restaurant = pInt(item.restaurant);

    if (cart.items.length && cart.restaurant_id && restaurant && cart.restaurant_id !== restaurant) {
      const ok = confirm("Tu carrito tiene items de otro restaurante. Vaciar carrito?");
      if (!ok) return null;
      cart.items = [];
      cart.restaurant_id = null;
    }

    if (restaurant && !cart.restaurant_id) {
      cart.restaurant_id = restaurant;
      localStorage.setItem(KEY.restaurant, String(restaurant));
    }

    const found = cart.items.find((x) => x.id === item.id);
    if (found) found.quantity += q;
    else {
      cart.items.push({
        id: item.id,
        name: item.name || "Producto",
        price_cop: Number(item.price_cop || 0),
        image_url: item.image_url || "",
        quantity: q,
        restaurant: restaurant,
        category: pInt(item.category)
      });
    }
    return saveCart(cart);
  }

  function setQty(id, qty) {
    const cart = readCart();
    const item = cart.items.find((x) => x.id === id);
    if (!item) return cart;
    if (qty <= 0) cart.items = cart.items.filter((x) => x.id !== id);
    else item.quantity = qty;
    if (!cart.items.length) cart.restaurant_id = null;
    return saveCart(cart);
  }

  function cartCount() {
    return readCart().items.reduce((a, i) => a + i.quantity, 0);
  }

  function cartSubtotal() {
    return readCart().items.reduce((a, i) => a + i.quantity * i.price_cop, 0);
  }

  function updateBadges() {
    const count = cartCount();
    const badges = [
      document.querySelector("a[href='./carrito.html'] span.absolute"),
      document.querySelector("header button span.absolute")
    ];
    badges.forEach((b) => {
      if (!b) return;
      if (count <= 0) {
        b.classList.add("hidden");
      } else {
        b.classList.remove("hidden");
        b.textContent = String(count);
      }
    });
  }

  function message(container, text, error) {
    if (!container) return;
    container.innerHTML = `<div class="rounded-xl border ${error ? "border-rose-300 bg-rose-50 text-rose-700" : "border-slate-200 bg-slate-50 text-slate-700"} p-4 text-sm">${esc(text)}</div>`;
  }

  function initIndex() {
    if (PAGE !== "index.html") return;
    const btn = Array.from(document.querySelectorAll("button")).find((b) => (b.textContent || "").toUpperCase().includes("VER MEN"));
    if (btn) btn.addEventListener("click", () => (location.href = "./menu.html"));
    updateBadges();
  }
  async function initMenu() {
    if (PAGE !== "menu.html") return;
    const navCats = document.querySelector("nav.px-4.py-4");
    const grid = document.querySelector("main .grid.grid-cols-2");
    const search = document.querySelector("input[placeholder*='Buscar']");
    if (!grid) return;

    grid.innerHTML = "<p class='col-span-2 text-sm text-slate-500'>Cargando menu...</p>";

    let cats = [];
    let items = [];
    let active = "";

    const forcedRestaurant = pInt(localStorage.getItem(KEY.restaurant));

    function renderCats() {
      if (!navCats) return;
      const base = "flex h-10 shrink-0 items-center justify-center gap-x-2 rounded-xl px-5 border transition-colors";
      const visible = cats.filter((c) => !forcedRestaurant || pInt(c.restaurant) === forcedRestaurant);
      const allBtn = `<button type="button" data-cat="" class="${base} ${active ? "bg-slate-200 dark:bg-primary/10 border-transparent text-slate-700 dark:text-slate-300" : "bg-primary border-primary text-background-dark"}"><span class="text-sm font-semibold">Todos</span></button>`;
      navCats.innerHTML = allBtn + visible.map((c) => {
        const id = pInt(c.id) || "";
        const on = String(id) === String(active);
        return `<button type="button" data-cat="${id}" class="${base} ${on ? "bg-primary border-primary text-background-dark" : "bg-slate-200 dark:bg-primary/10 border-transparent text-slate-700 dark:text-slate-300"}"><span class="text-sm font-semibold">${esc(c.name || "Categoria")}</span></button>`;
      }).join("");
    }

    function card(item) {
      const image = esc(item.image_url || "https://placehold.co/600x600?text=Noah+Food");
      return `<article class="bg-white dark:bg-primary/5 rounded-xl overflow-hidden border border-slate-100 dark:border-primary/10 shadow-sm flex flex-col" data-id="${item.id}">
        <a href="./detalle.html?id=${item.id}" class="aspect-square bg-slate-200 dark:bg-primary/20 block"><img alt="${esc(item.name)}" src="${image}" class="w-full h-full object-cover" loading="lazy" /></a>
        <div class="p-3 flex flex-col flex-1">
          <a href="./detalle.html?id=${item.id}" class="font-bold text-sm mb-1 line-clamp-1 hover:text-primary transition-colors">${esc(item.name || "Producto")}</a>
          <p class="text-xs text-slate-500 dark:text-slate-400 line-clamp-2 flex-1 mb-2">${esc(item.description || "Sin descripcion")}</p>
          <div class="flex items-center justify-between mt-auto pt-2">
            <span class="font-bold text-primary">${cop(item.price_cop || 0)}</span>
            <button type="button" data-add="${item.id}" class="bg-primary text-background-dark p-1.5 rounded-lg flex items-center justify-center"><span class="material-symbols-outlined text-base">add</span></button>
          </div>
        </div>
      </article>`;
    }

    function renderGrid() {
      const q = (search?.value || "").toLowerCase().trim();
      const list = items.filter((i) => {
        if (forcedRestaurant && pInt(i.restaurant) !== forcedRestaurant) return false;
        if (active && String(i.category || "") !== String(active)) return false;
        if (!q) return true;
        const text = `${i.name || ""} ${i.description || ""} ${i.category_name || ""}`.toLowerCase();
        return text.includes(q);
      });

      if (!list.length) {
        message(grid, "No hay productos para esos filtros.", false);
        return;
      }
      grid.innerHTML = list.map(card).join("");
    }

    try {
      [cats, items] = await Promise.all([api.listCategories(), api.listMenuItems()]);
      cats = cats.filter((c) => c.is_active !== false);
      items = items.filter((i) => i.is_active !== false);
      renderCats();
      renderGrid();
    } catch (e) {
      message(grid, `No se pudo cargar el menu: ${e.message}`, true);
      return;
    }

    navCats?.addEventListener("click", (ev) => {
      const btn = ev.target.closest("button[data-cat]");
      if (!btn) return;
      active = btn.dataset.cat || "";
      renderCats();
      renderGrid();
    });

    search?.addEventListener("input", renderGrid);

    grid.addEventListener("click", (ev) => {
      const btn = ev.target.closest("button[data-add]");
      if (!btn) return;
      const id = pInt(btn.dataset.add);
      const item = items.find((x) => pInt(x.id) === id);
      if (!item) return;
      const ok = addCart(item, 1);
      if (!ok) return;
      updateBadges();
    });

    updateBadges();
  }

  async function initDetail() {
    if (PAGE !== "detalle.html") return;

    const params = new URLSearchParams(location.search);
    const id = pInt(params.get("id")) || pInt(localStorage.getItem(KEY.lastItem));
    const title = document.querySelector("h1");
    const price = document.querySelector("h2");
    const desc = document.querySelector("div.mt-6 p");
    const hero = document.querySelector("div.w-full.h-full.bg-center.bg-no-repeat.bg-cover");
    const qtyEl = document.querySelector("div.fixed.bottom-0 span.text-lg.font-bold");
    const minus = qtyEl?.previousElementSibling;
    const plus = qtyEl?.nextElementSibling;
    const addBtn = document.querySelector("div.fixed.bottom-0 button.flex-1");

    if (!id) {
      if (title) title.textContent = "Producto no encontrado";
      if (desc) desc.textContent = "Selecciona un producto desde el menu.";
      if (price) price.textContent = cop(0);
      if (addBtn) addBtn.disabled = true;
      return;
    }

    let item = null;
    let qty = 1;
    const syncQty = () => {
      if (qtyEl) qtyEl.textContent = String(qty);
    };
    syncQty();

    minus?.addEventListener("click", () => {
      qty = Math.max(1, qty - 1);
      syncQty();
    });
    plus?.addEventListener("click", () => {
      qty += 1;
      syncQty();
    });

    try {
      item = await api.getMenuItem(id);
      localStorage.setItem(KEY.lastItem, String(id));
      if (title) title.textContent = item.name || "Producto";
      if (price) price.textContent = cop(item.price_cop || 0);
      if (desc) desc.textContent = item.description || "Sin descripcion";
      if (hero && item.image_url) hero.style.backgroundImage = `url('${item.image_url}')`;
    } catch (e) {
      if (title) title.textContent = "No se pudo cargar";
      if (desc) desc.textContent = e.message;
      if (addBtn) addBtn.disabled = true;
      return;
    }

    addBtn?.addEventListener("click", () => {
      if (!item) return;
      const ok = addCart(item, qty);
      if (!ok) return;
      location.href = "./carrito.html";
    });
  }

  function initCart() {
    if (PAGE !== "carrito.html") return;

    const main = document.querySelector("main");
    const summary = document.querySelector("section.mt-auto");
    if (!main || !summary) return;

    function row(item) {
      return `<article class="flex items-center gap-4 bg-white dark:bg-primary/5 p-3 rounded-xl border border-slate-200 dark:border-primary/10" data-id="${item.id}">
        <div class="h-20 w-20 shrink-0 overflow-hidden rounded-lg bg-slate-100 dark:bg-slate-800"><img alt="${esc(item.name)}" class="h-full w-full object-cover" src="${esc(item.image_url || "https://placehold.co/200x200?text=Noah")}" /></div>
        <div class="flex flex-1 flex-col justify-between self-stretch">
          <div class="flex justify-between items-start"><div><h3 class="font-semibold text-base leading-tight">${esc(item.name)}</h3><p class="text-sm text-slate-500 dark:text-primary/60 mt-1">${cop(item.price_cop)}</p></div><button type="button" data-remove="${item.id}" class="text-slate-400 hover:text-red-500"><span class="material-symbols-outlined text-[20px]">delete</span></button></div>
          <div class="flex items-center justify-end"><div class="flex items-center gap-3 bg-slate-100 dark:bg-primary/20 px-3 py-1 rounded-full"><button type="button" data-dec="${item.id}" class="flex h-6 w-6 items-center justify-center rounded-full text-slate-900 dark:text-primary hover:bg-primary hover:text-white">-</button><span class="text-sm font-bold w-6 text-center">${item.quantity}</span><button type="button" data-inc="${item.id}" class="flex h-6 w-6 items-center justify-center rounded-full text-slate-900 dark:text-primary hover:bg-primary hover:text-white">+</button></div></div>
        </div>
      </article>`;
    }

    function render() {
      const cart = readCart();
      const subtotal = cartSubtotal();
      if (!cart.items.length) {
        main.innerHTML = `<div class="rounded-xl border border-slate-200 dark:border-primary/20 bg-white dark:bg-primary/5 p-6 text-center"><p class="text-base font-semibold mb-2">Tu carrito esta vacio</p><a href="./menu.html" class="inline-flex items-center justify-center rounded-xl bg-primary px-4 py-2 font-bold text-background-dark">Ir al menu</a></div>`;
      } else {
        main.innerHTML = cart.items.map(row).join("");
      }

      summary.innerHTML = `<div class="space-y-2"><div class="flex justify-between text-slate-500 dark:text-primary/70"><span>Subtotal</span><span>${cop(subtotal)}</span></div><div class="flex justify-between text-slate-500 dark:text-primary/70"><span>Envio</span><span class="text-primary font-medium">Se calcula al confirmar</span></div><div class="flex justify-between text-lg font-bold pt-2 border-t border-slate-100 dark:border-primary/10"><span>Total estimado</span><span class="text-primary">${cop(subtotal)}</span></div></div><button type="button" data-checkout class="w-full bg-primary py-4 rounded-xl text-background-dark font-bold text-lg ${cart.items.length ? "" : "opacity-50 cursor-not-allowed"}" ${cart.items.length ? "" : "disabled"}>Ir a pagar</button>`;
      updateBadges();
    }

    main.addEventListener("click", (ev) => {
      const inc = ev.target.closest("button[data-inc]");
      const dec = ev.target.closest("button[data-dec]");
      const rem = ev.target.closest("button[data-remove]");
      if (!inc && !dec && !rem) return;
      const id = pInt((inc || dec || rem).dataset.inc || (inc || dec || rem).dataset.dec || (inc || dec || rem).dataset.remove);
      const cart = readCart();
      const item = cart.items.find((x) => x.id === id);
      if (!item) return;
      if (inc) setQty(id, item.quantity + 1);
      if (dec) setQty(id, item.quantity - 1);
      if (rem) setQty(id, 0);
      render();
    });

    summary.addEventListener("click", (ev) => {
      if (ev.target.closest("button[data-checkout]")) location.href = "./checkout.html";
    });

    render();
  }
  function initCheckout() {
    if (PAGE !== "checkout.html") return;

    const summaryRoot = document.querySelector("div.px-4.py-4.mb-32");
    const summaryList = summaryRoot?.querySelector(".flex.flex-col.gap-3");
    const notes = document.querySelector("textarea");
    const button = document.querySelector("div.fixed.bottom-0 button");

    const feedback = document.createElement("div");
    feedback.className = "px-4 pb-2 text-sm";
    summaryRoot?.prepend(feedback);

    function setFeedback(text, error) {
      feedback.innerHTML = text ? `<div class="rounded-xl border ${error ? "border-rose-300 bg-rose-50 text-rose-700" : "border-emerald-300 bg-emerald-50 text-emerald-700"} p-3">${esc(text)}</div>` : "";
    }

    function render() {
      const cart = readCart();
      const subtotal = cartSubtotal();
      if (!summaryList) return;

      if (!cart.items.length) {
        summaryList.innerHTML = `<div class="rounded-xl border border-slate-200 dark:border-primary/20 bg-white dark:bg-primary/5 p-4 text-sm text-slate-600 dark:text-slate-300">Tu carrito esta vacio. Regresa al menu para agregar productos.</div>`;
        if (button) {
          button.disabled = true;
          button.classList.add("opacity-50", "cursor-not-allowed");
        }
        return;
      }

      summaryList.innerHTML = cart.items.map((i) => `<div class="flex justify-between items-center"><span class="text-slate-500 dark:text-slate-400">${i.quantity}x ${esc(i.name)}</span><span class="text-slate-900 dark:text-slate-100 font-medium">${cop(i.quantity * i.price_cop)}</span></div>`).join("") + `<div class="flex justify-between items-center"><span class="text-slate-500 dark:text-slate-400">Envio</span><span class="text-slate-900 dark:text-slate-100 font-medium">Se calcula en backend</span></div><div class="h-px bg-slate-200 dark:bg-primary/20 my-2"></div><div class="flex justify-between items-center"><span class="text-slate-900 dark:text-slate-100 font-bold">Total estimado</span><span class="text-primary text-xl font-bold">${cop(subtotal)}</span></div>`;

      if (button) {
        button.disabled = false;
        button.classList.remove("opacity-50", "cursor-not-allowed");
      }
    }

    async function submit() {
      const cart = readCart();
      if (!cart.items.length) return;

      const restaurant = cart.restaurant_id || pInt(localStorage.getItem(KEY.restaurant)) || pInt(cart.items[0]?.restaurant);
      if (!restaurant) {
        setFeedback("No se pudo determinar el restaurante del pedido.", true);
        return;
      }

      const payload = {
        restaurant,
        channel: "web",
        customer_notes: (notes?.value || "").trim(),
        items: cart.items.map((i) => ({ menu_item_id: i.id, quantity: i.quantity }))
      };

      if (button) {
        button.disabled = true;
        button.classList.add("opacity-70");
      }

      setFeedback("", false);

      try {
        const order = await api.createOrder(payload);
        if (order?.id) localStorage.setItem(KEY.lastOrder, String(order.id));
        saveCart({ restaurant_id: null, items: [] });
        setFeedback("Pedido creado correctamente. Redirigiendo...", false);
        setTimeout(() => {
          location.href = order?.id ? `./estado.html?order_id=${order.id}` : "./estado.html";
        }, 600);
      } catch (e) {
        if (button) {
          button.disabled = false;
          button.classList.remove("opacity-70");
        }
        const msg = (e.status === 401 || e.status === 403)
          ? "Debes iniciar sesion desde Perfil para confirmar pedidos."
          : e.message;
        setFeedback(msg, true);
      }
    }

    button?.addEventListener("click", submit);
    render();
  }

  async function initEstado() {
    if (PAGE !== "estado.html") return;

    const params = new URLSearchParams(location.search);
    const id = pInt(params.get("order_id") || params.get("id")) || pInt(localStorage.getItem(KEY.lastOrder));

    const idEl = document.querySelector("section p.text-2xl.font-bold");
    const badge = document.querySelector("section div.rounded-full");
    const title = document.querySelector("section p.text-lg.font-bold");
    const meta = document.querySelector("section p.text-slate-500");
    const timeline = document.querySelectorAll("main section")[1];

    let order = null;

    try {
      if (id) order = await api.getOrder(id);
      else {
        const list = await api.listOrders();
        order = list[0] || null;
      }
    } catch (e) {
      message(timeline, (e.status === 401 || e.status === 403)
        ? "No autorizado para consultar pedidos. Inicia sesion en Perfil."
        : `No se pudo consultar pedido: ${e.message}`, true);
      return;
    }

    if (!order) {
      message(timeline, "No hay pedidos para mostrar.", false);
      return;
    }

    if (order.id) localStorage.setItem(KEY.lastOrder, String(order.id));

    if (idEl) idEl.textContent = `#${order.order_number || order.id}`;

    const statusMap = {
      PENDING: "PENDIENTE",
      IN_PROGRESS: "EN PREPARACION",
      READY: "LISTO",
      COMPLETED: "ENTREGADO",
      CANCELLED: "CANCELADO"
    };
    const status = order.status || "PENDING";
    const statusText = statusMap[status] || status;

    if (badge) {
      badge.textContent = statusText;
      badge.className = "px-3 py-1 rounded-full text-xs font-bold border bg-primary/10 text-primary border-primary/30";
      if (status === "COMPLETED") badge.className = "px-3 py-1 rounded-full text-xs font-bold border bg-emerald-500/10 text-emerald-600 border-emerald-500/30";
      if (status === "CANCELLED") badge.className = "px-3 py-1 rounded-full text-xs font-bold border bg-rose-500/10 text-rose-600 border-rose-500/30";
    }

    if (title) {
      const names = (order.items || []).map((i) => i.menu_item_name).filter(Boolean);
      title.textContent = names.length ? names.slice(0, 2).join(" + ") : "Pedido Noah Food";
    }

    if (meta) {
      const qty = (order.items || []).reduce((a, i) => a + Number(i.quantity || 0), 0);
      meta.textContent = `${qty} items - ${cop(order.total_cop || 0)}`;
    }

    if (timeline) {
      const steps = [
        { name: "Nuevo", done: true, at: order.pending_at || order.created_at || "Pendiente" },
        { name: "Preparacion", done: ["IN_PROGRESS", "READY", "COMPLETED"].includes(status), at: order.in_progress_at || "Pendiente" },
        { name: "Listo", done: ["READY", "COMPLETED"].includes(status), at: order.ready_at || "Pendiente" },
        { name: "Entregado", done: status === "COMPLETED", at: order.completed_at || "Pendiente" }
      ];

      timeline.innerHTML = `<div class="rounded-xl border border-slate-200 dark:border-slate-700 p-4 bg-white dark:bg-slate-900/40"><div class="space-y-4">${steps.map((s) => `<div class="flex items-start gap-3 ${s.done ? "" : "opacity-75"}"><div class="mt-0.5 h-7 w-7 rounded-full flex items-center justify-center ${s.done ? "bg-primary text-background-dark" : "bg-slate-200 dark:bg-slate-800 text-slate-500"}"><span class="material-symbols-outlined text-[16px]">${s.done ? "check" : "radio_button_unchecked"}</span></div><div><p class="${s.done ? "text-slate-900 dark:text-slate-100 font-semibold" : "text-slate-500 dark:text-slate-400"}">${s.name}</p><p class="text-xs text-slate-500 dark:text-slate-400">${s.at}</p></div></div>`).join("")}${status === "CANCELLED" ? '<div class="mt-3 rounded-lg border border-rose-300 bg-rose-50 text-rose-700 p-3 text-sm">Este pedido fue cancelado.</div>' : ""}</div></div>`;
    }
  }

  async function initPerfil() {
    if (PAGE !== "perfil.html") return;

    const nameEl = document.querySelector("section h1");
    const subtitleEl = document.querySelector("section p.text-slate-500");
    const ordersWrap = document.querySelector("div.flex.flex-col.gap-4.p-4.mb-24");
    const settingsBtn = document.querySelector("header button");

    if (!ordersWrap) return;

    function fmt(dateText) {
      if (!dateText) return "Fecha no disponible";
      const d = new Date(dateText);
      if (Number.isNaN(d.getTime())) return dateText;
      return new Intl.DateTimeFormat("es-CO", { dateStyle: "medium", timeStyle: "short" }).format(d);
    }

    function setHeaderMode(loggedIn) {
      if (!settingsBtn) return;
      settingsBtn.dataset.mode = loggedIn ? "logout" : "login";
      settingsBtn.title = loggedIn ? "Cerrar sesion" : "Iniciar sesion";
      const icon = settingsBtn.querySelector("span.material-symbols-outlined");
      if (icon) icon.textContent = loggedIn ? "logout" : "login";
    }

    function renderLoginForm(text) {
      ordersWrap.innerHTML = `
        <form id="profile-login-form" class="rounded-xl bg-slate-100 dark:bg-primary/5 p-4 border border-slate-200 dark:border-primary/10 space-y-3">
          <h3 class="text-base font-bold">Inicia sesion</h3>
          <input id="profile-login-username" name="username" type="text" placeholder="Usuario" class="w-full rounded-lg border border-slate-200 dark:border-primary/20 bg-white dark:bg-primary/10 px-3 py-2 text-sm" required />
          <input id="profile-login-password" name="password" type="password" placeholder="Contraseña" class="w-full rounded-lg border border-slate-200 dark:border-primary/20 bg-white dark:bg-primary/10 px-3 py-2 text-sm" required />
          <button type="submit" class="w-full rounded-lg bg-primary text-background-dark font-bold py-2">Entrar</button>
          ${text ? `<p class="text-xs ${text.includes("Error") ? "text-rose-500" : "text-slate-500 dark:text-slate-400"}">${esc(text)}</p>` : ""}
        </form>
      `;

      const form = document.getElementById("profile-login-form");
      form?.addEventListener("submit", async (ev) => {
        ev.preventDefault();
        const username = String(form.username?.value || "").trim();
        const password = String(form.password?.value || "");

        if (!username || !password) {
          renderLoginForm("Usuario y contraseña son obligatorios.");
          return;
        }

        const submitButton = form.querySelector("button[type='submit']");
        if (submitButton) submitButton.disabled = true;

        try {
          const result = await api.login(username, password);
          saveAuthToken(result?.token || "");
          if (result?.user?.customer_id) localStorage.setItem("noah_customer_id", String(result.user.customer_id));
          await loadAuthenticatedProfile();
        } catch (e) {
          renderLoginForm(`Error de inicio de sesion: ${e.message}`);
        } finally {
          if (submitButton) submitButton.disabled = false;
        }
      });
    }

    function renderOrders(orders) {
      if (!orders.length) {
        message(ordersWrap, "No tienes pedidos aun.", false);
        return;
      }

      const statusMap = {
        PENDING: "PENDIENTE",
        IN_PROGRESS: "EN PREPARACION",
        READY: "LISTO",
        COMPLETED: "ENTREGADO",
        CANCELLED: "CANCELADO"
      };

      ordersWrap.innerHTML = orders.slice(0, 10).map((order) => {
        const qty = (order.items || []).reduce((a, i) => a + Number(i.quantity || 0), 0);
        const status = statusMap[order.status] || (order.status || "SIN ESTADO");
        const statusColor = order.status === "COMPLETED"
          ? "text-emerald-500"
          : order.status === "CANCELLED"
          ? "text-rose-500"
          : "text-primary";

        return `
          <article class="flex flex-col gap-3 rounded-xl bg-slate-100 dark:bg-primary/5 p-4 border border-slate-200 dark:border-primary/10">
            <div class="flex items-center justify-between gap-3">
              <p class="text-xs font-bold tracking-wide ${statusColor}">${status}</p>
              <p class="text-xs text-slate-500 dark:text-slate-400">${fmt(order.created_at)}</p>
            </div>
            <p class="text-slate-900 dark:text-slate-100 text-lg font-bold leading-tight">Pedido #${esc(order.order_number || order.id)}</p>
            <p class="text-slate-600 dark:text-slate-400 text-sm">${qty} items - ${cop(order.total_cop || 0)}</p>
            <a href="./estado.html?order_id=${order.id}" class="inline-flex items-center justify-center gap-2 rounded-lg h-10 bg-primary text-background-dark text-sm font-bold">Ver estado</a>
          </article>
        `;
      }).join("");
    }

    async function loadAuthenticatedProfile() {
      try {
        const me = await api.me();
        const user = me?.user || {};

        if (nameEl) nameEl.textContent = user.customer_name || user.username || "Usuario";
        if (subtitleEl) subtitleEl.textContent = user.email || user.username || "";

        setHeaderMode(true);

        const orders = await api.listOrders();
        renderOrders(orders);
      } catch (e) {
        if (e.status === 401 || e.status === 403) {
          saveAuthToken("");
          setHeaderMode(false);
          if (nameEl) nameEl.textContent = "Invitado";
          if (subtitleEl) subtitleEl.textContent = "Inicia sesion para ver tu perfil";
          renderLoginForm("Inicia sesion para ver historial y pagar pedidos.");
          return;
        }
        message(ordersWrap, `No se pudo cargar el perfil: ${e.message}`, true);
      }
    }

    settingsBtn?.addEventListener("click", async () => {
      if ((settingsBtn.dataset.mode || "") !== "logout") {
        document.getElementById("profile-login-username")?.focus();
        return;
      }
      try {
        await api.logout();
      } catch (e) {
        // Si el token ya no existe en backend, igual limpiamos localmente.
      }
      saveAuthToken("");
      setHeaderMode(false);
      if (nameEl) nameEl.textContent = "Invitado";
      if (subtitleEl) subtitleEl.textContent = "Inicia sesion para ver tu perfil";
      renderLoginForm("Sesion cerrada correctamente.");
    });

    await loadAuthenticatedProfile();
  }

  async function boot() {
    initIndex();
    await initMenu();
    await initDetail();
    initCart();
    initCheckout();
    await initEstado();
    await initPerfil();
    updateBadges();
  }

  document.addEventListener("DOMContentLoaded", () => {
    boot().catch((e) => console.error("Frontend boot error:", e));
  });
})();
