import "./styles.css";

const API_BASE = (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

const state = {
  categories: [],
  products: [],
  pagination: null,
  listFilters: {
    q: "",
    category: "",
    in_stock: false,
    min_price: "",
    max_price: "",
    sort_by: "relevance",
    page: 1,
    page_size: 24
  },
  productDetail: null,
  relatedProducts: [],
  recommendations: [],
  imageResults: [],
  cart: loadCart(),
  loading: {
    categories: false,
    products: false,
    detail: false,
    recommendations: false,
    imageSearch: false,
    quote: false
  },
  error: ""
};

const sortOptions = [
  { label: "Relevance", value: "relevance" },
  { label: "Newest", value: "newest" },
  { label: "Price: Low to High", value: "price_asc" },
  { label: "Price: High to Low", value: "price_desc" },
  { label: "Title: A-Z", value: "title_asc" }
];

function route() {
  const hash = window.location.hash || "#/";
  if (hash.startsWith("#/catalog")) return "catalog";
  if (hash.startsWith("#/product/")) return "product";
  return "home";
}

function parseCatalogParams() {
  const hash = window.location.hash || "#/catalog";
  const queryString = hash.includes("?") ? hash.split("?")[1] : "";
  const params = new URLSearchParams(queryString);
  return {
    q: params.get("q") || "",
    category: params.get("category") || "",
    in_stock: params.get("in_stock") === "true",
    min_price: params.get("min_price") || "",
    max_price: params.get("max_price") || "",
    sort_by: params.get("sort_by") || "relevance",
    page: Number(params.get("page") || "1"),
    page_size: 24
  };
}

function updateCatalogHash() {
  const params = new URLSearchParams();
  if (state.listFilters.q) params.set("q", state.listFilters.q);
  if (state.listFilters.category) params.set("category", state.listFilters.category);
  if (state.listFilters.in_stock) params.set("in_stock", "true");
  if (state.listFilters.min_price) params.set("min_price", state.listFilters.min_price);
  if (state.listFilters.max_price) params.set("max_price", state.listFilters.max_price);
  if (state.listFilters.sort_by && state.listFilters.sort_by !== "relevance") {
    params.set("sort_by", state.listFilters.sort_by);
  }
  if (state.listFilters.page > 1) params.set("page", String(state.listFilters.page));
  const suffix = params.toString() ? `?${params.toString()}` : "";
  const next = `#/catalog${suffix}`;
  if (window.location.hash !== next) {
    window.location.hash = next;
  }
}

function loadCart() {
  try {
    const raw = localStorage.getItem("vx_cart");
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveCart() {
  localStorage.setItem("vx_cart", JSON.stringify(state.cart));
}

function cartTotal() {
  return state.cart.reduce((sum, item) => sum + (item.price || 0) * item.qty, 0);
}

function countCartItems() {
  return state.cart.reduce((sum, item) => sum + item.qty, 0);
}

function toCurrency(value, currency = "USD") {
  if (value === null || value === undefined) return "Quote on request";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 2
  }).format(value);
}

function imageUrl(url) {
  if (!url) return "https://via.placeholder.com/640x400?text=No+Image";
  if (url.startsWith("http://") || url.startsWith("https://")) return url;
  return `${API_BASE}${url}`;
}

function categoryChipsHtml(selectedCategory) {
  return `
    <button class="chip ${selectedCategory ? "" : "active"}" data-category="">
      All
    </button>
    ${state.categories
      .map(
        (cat) => `
          <button class="chip ${selectedCategory === cat.slug ? "active" : ""}" data-category="${cat.slug}">
            ${cat.name}
          </button>
        `
      )
      .join("")}
  `;
}

function productCardHtml(product) {
  return `
    <article class="product-card">
      <a href="#/product/${product.id}" class="product-media">
        <img src="${imageUrl(product.thumbnail)}" alt="${product.title}" loading="lazy" />
      </a>
      <div class="product-content">
        <p class="stock ${product.in_stock ? "ok" : "warn"}">${product.in_stock ? "In stock" : "Out of stock"}</p>
        <h3><a href="#/product/${product.id}">${product.title}</a></h3>
        <p class="sku">${product.sku || "SKU N/A"}</p>
        <div class="card-foot">
          <p class="price">${toCurrency(product.price, product.currency)}</p>
          <button class="btn-mini" data-add-to-cart="${product.id}">Add</button>
        </div>
      </div>
    </article>
  `;
}

function headerCategoryNavHtml() {
  const featured = state.categories.slice(0, 8);
  return `
    <a class="menu-link ${state.listFilters.category ? "" : "active"}" href="#/catalog">All Categories</a>
    ${featured
      .map(
        (category) => `
          <a
            class="menu-link ${state.listFilters.category === category.slug ? "active" : ""}"
            href="#/catalog?category=${encodeURIComponent(category.slug)}"
          >
            ${category.name}
          </a>
        `
      )
      .join("")}
  `;
}

function topNavHtml() {
  return `
    <header class="site-header">
      <div class="mode-strip">
        <button type="button" class="mode-btn active">Scheduled</button>
        <button type="button" class="mode-btn">Express</button>
      </div>

      <div class="core-strip">
        <a class="brand" href="#/">
          <span class="brand-mark">VX</span>
          <span>
            <strong>Vortexus Industrial</strong>
            <small>Water Treatment, Boreholes, Pumps</small>
          </span>
        </a>

        <div class="delivery-badge">
          <span class="slot">Today 1:00 PM</span>
          <span class="location">Westlands - Nairobi</span>
        </div>

        <form id="header-search-form" class="header-search">
          <input
            id="header-search-input"
            type="search"
            placeholder="Search pumps, treatment systems, spares..."
            value="${state.listFilters.q || ""}"
          />
          <button type="submit" aria-label="Search">Search</button>
        </form>

        <a class="account-link" href="${API_BASE}/accounts/login/" target="_blank" rel="noreferrer">Login & Register</a>
        <a class="cart-pill" href="#/catalog">Cart ${countCartItems()}</a>
      </div>

      <nav class="menu-strip">
        ${headerCategoryNavHtml()}
      </nav>
    </header>
  `;
}

function homeViewHtml() {
  return `
    <section class="hero">
      <div class="hero-copy">
        <h1>Industrial Ecommerce for Water Projects</h1>
        <p>
          Source borehole pumps, treatment systems and accessories quickly with fast text search,
          image search and recommendation rails.
        </p>
      </div>
      <form id="hero-search-form" class="hero-search">
        <input
          id="hero-search-input"
          name="q"
          type="search"
          placeholder="Search by model, duty point or brand"
          value="${state.listFilters.q}"
        />
        <button type="submit">Search Catalog</button>
      </form>
      <div class="chip-row" id="home-chips">
        ${categoryChipsHtml(state.listFilters.category)}
      </div>
    </section>

    <section class="panel" id="recommendations">
      <div class="panel-head">
        <h2>Trending Recommendations</h2>
        <p>${state.loading.recommendations ? "Loading..." : `Items tailored from ${state.recommendations.length ? "live data" : "catalog fallback"}`}</p>
      </div>
      ${
        state.recommendations.length
          ? `<div class="product-grid">${state.recommendations.map(productCardHtml).join("")}</div>`
          : `<p class="empty">No recommendations yet.</p>`
      }
    </section>

    <section class="panel" id="image-search">
      <div class="panel-head">
        <h2>Image Search</h2>
        <p>Upload a part photo and match similar products.</p>
      </div>
      <form id="image-search-form" class="image-form">
        <input type="file" name="image" accept="image/*" required />
        <button type="submit">${state.loading.imageSearch ? "Searching..." : "Find Matches"}</button>
      </form>
      ${
        state.imageResults.length
          ? `<div class="product-grid">${state.imageResults.map(productCardHtml).join("")}</div>`
          : `<p class="empty">No image matches yet.</p>`
      }
    </section>
  `;
}

function catalogViewHtml() {
  const sortSelectOptions = sortOptions
    .map((option) => `<option value="${option.value}" ${option.value === state.listFilters.sort_by ? "selected" : ""}>${option.label}</option>`)
    .join("");

  return `
    <section class="panel catalog-shell">
      <div class="panel-head">
        <h2>Industrial Catalog</h2>
        <p>
          ${state.pagination ? `${state.pagination.total} products` : "Loading products..."}
        </p>
      </div>

      <div class="chip-row" id="catalog-chips">
        ${categoryChipsHtml(state.listFilters.category)}
      </div>

      <div class="catalog-layout">
        <aside class="filters">
          <form id="catalog-filter-form">
            <label>
              Search
              <input type="search" name="q" value="${state.listFilters.q}" placeholder="pump, UV, pressure tank" />
            </label>
            <label>
              Min Price
              <input type="number" step="0.01" min="0" name="min_price" value="${state.listFilters.min_price}" />
            </label>
            <label>
              Max Price
              <input type="number" step="0.01" min="0" name="max_price" value="${state.listFilters.max_price}" />
            </label>
            <label class="inline-check">
              <input type="checkbox" name="in_stock" ${state.listFilters.in_stock ? "checked" : ""} />
              In stock only
            </label>
            <button type="submit">${state.loading.products ? "Applying..." : "Apply Filters"}</button>
          </form>
        </aside>

        <div class="catalog-main">
          <div class="list-toolbar">
            <label>
              Sort by
              <select id="sort-by">${sortSelectOptions}</select>
            </label>
          </div>

          ${
            state.products.length
              ? `<div class="product-grid">${state.products.map(productCardHtml).join("")}</div>`
              : `<p class="empty">No products found with these filters.</p>`
          }

          ${
            state.pagination?.has_next
              ? `<button id="load-more-btn" class="load-more">${state.loading.products ? "Loading..." : "Load More"}</button>`
              : ""
          }
        </div>
      </div>
    </section>
  `;
}

function specificationRows(specs) {
  if (!specs || !specs.length) return `<p class="empty">No technical specs added yet.</p>`;
  return `
    <table class="spec-table">
      <tbody>
        ${specs
          .map(
            (spec) => `
              <tr>
                <th>${spec.name}</th>
                <td>${spec.value}</td>
              </tr>
            `
          )
          .join("")}
      </tbody>
    </table>
  `;
}

function productViewHtml() {
  if (!state.productDetail) {
    return `<section class="panel"><p class="empty">Loading product details...</p></section>`;
  }
  const product = state.productDetail;
  const image = product.primary_image || product.thumbnail;
  return `
    <section class="panel product-page">
      <a class="back-link" href="#/catalog">← Back to catalog</a>
      <div class="product-layout">
        <div class="product-media-lg">
          <img src="${imageUrl(image)}" alt="${product.title}" />
        </div>
        <div class="product-info">
          <h1>${product.title}</h1>
          <p class="sku">${product.sku || "SKU N/A"}</p>
          <p class="price-lg">${toCurrency(product.price, product.currency)}</p>
          <p class="stock ${product.in_stock ? "ok" : "warn"}">${product.in_stock ? "Available now" : "Made to order / out of stock"}</p>
          <p class="desc">${product.description || "No product description available."}</p>
          ${
            product.categories?.length
              ? `<p class="meta-line">Categories: ${product.categories.map((cat) => cat.name).join(", ")}</p>`
              : ""
          }

          <div class="desktop-actions">
            <button class="primary-btn" data-detail-add="${product.id}">Add to Cart</button>
            <button class="secondary-btn" id="open-quote-btn">Request Quote</button>
          </div>
        </div>
      </div>

      <section class="sub-panel">
        <h2>Technical Specifications</h2>
        ${specificationRows(product.specifications)}
      </section>

      <section class="sub-panel">
        <h2>Frequently Bought Together</h2>
        ${
          state.relatedProducts.length
            ? `<div class="product-grid">${state.relatedProducts.map(productCardHtml).join("")}</div>`
            : `<p class="empty">No related products available.</p>`
        }
      </section>
    </section>

    <div class="sticky-actions">
      <span>
        ${toCurrency(product.price, product.currency)}
      </span>
      <button class="primary-btn" data-detail-add="${product.id}">Add to Cart</button>
      <button class="secondary-btn" id="open-quote-btn-mobile">Quote</button>
    </div>

    <dialog id="quote-dialog">
      <form id="quote-form" method="dialog">
        <h3>Request Quote</h3>
        <p>Product: <strong>${product.title}</strong></p>
        <label>
          Name
          <input type="text" name="name" required />
        </label>
        <label>
          Email
          <input type="email" name="email" />
        </label>
        <label>
          Phone
          <input type="text" name="phone" />
        </label>
        <label>
          Company
          <input type="text" name="company" />
        </label>
        <label>
          Requirement
          <textarea name="message" rows="4" required placeholder="Project location, flow/head, delivery timeline..."></textarea>
        </label>
        <div class="dialog-actions">
          <button type="button" id="close-quote-btn">Cancel</button>
          <button type="submit">${state.loading.quote ? "Sending..." : "Send Quote Request"}</button>
        </div>
      </form>
    </dialog>
  `;
}

function footerHtml() {
  return `
    <footer class="footer">
      <div>
        <strong>Cart Total:</strong> ${toCurrency(cartTotal())}
      </div>
      <div class="muted">
        Built for industrial procurement: pumps, boreholes, treatment systems, and accessories.
      </div>
    </footer>
  `;
}

function appShellHtml(contentHtml) {
  return `
    <div class="app-shell">
      ${topNavHtml()}
      <main class="main">${contentHtml}</main>
      ${footerHtml()}
      ${state.error ? `<p class="error-banner">${state.error}</p>` : ""}
    </div>
  `;
}

function render() {
  const app = document.querySelector("#app");
  let content = "";
  const current = route();
  if (current === "catalog") content = catalogViewHtml();
  else if (current === "product") content = productViewHtml();
  else content = homeViewHtml();
  app.innerHTML = appShellHtml(content);
  bindEvents();
}

function navigateToCatalog(extra = {}) {
  const previousHash = window.location.hash;
  state.listFilters = {
    ...state.listFilters,
    ...extra,
    page: extra.page || 1
  };
  updateCatalogHash();
  if (route() === "catalog" && previousHash === window.location.hash) {
    void fetchProducts();
  }
}

function addToCart(product) {
  const existing = state.cart.find((item) => item.id === product.id);
  if (existing) {
    existing.qty += 1;
  } else {
    state.cart.push({
      id: product.id,
      title: product.title,
      price: product.price || 0,
      currency: product.currency || "USD",
      qty: 1
    });
  }
  saveCart();
  render();
}

async function fetchCategories() {
  state.loading.categories = true;
  try {
    const response = await fetch(`${API_BASE}/api/v1/catalog/categories/`);
    if (!response.ok) throw new Error(`Category load failed (${response.status})`);
    const payload = await response.json();
    state.categories = payload.results || [];
  } catch (error) {
    state.error = String(error);
  } finally {
    state.loading.categories = false;
  }
}

async function fetchProducts({ append = false } = {}) {
  state.loading.products = true;
  state.error = "";
  render();
  try {
    const params = new URLSearchParams();
    Object.entries(state.listFilters).forEach(([key, value]) => {
      if (value === "" || value === false || value === null || value === undefined) return;
      params.set(key, String(value));
    });
    const response = await fetch(`${API_BASE}/api/v1/catalog/products/?${params.toString()}`);
    if (!response.ok) throw new Error(`Product list failed (${response.status})`);
    const payload = await response.json();
    if (append) state.products = [...state.products, ...(payload.results || [])];
    else state.products = payload.results || [];
    state.pagination = payload.pagination || null;
  } catch (error) {
    state.error = String(error);
  } finally {
    state.loading.products = false;
    render();
  }
}

async function fetchRecommendations() {
  state.loading.recommendations = true;
  try {
    const response = await fetch(`${API_BASE}/api/v1/recommendations/?limit=8`);
    if (!response.ok) throw new Error(`Recommendations failed (${response.status})`);
    const payload = await response.json();
    state.recommendations = payload.results || [];
  } catch (error) {
    state.error = String(error);
  } finally {
    state.loading.recommendations = false;
  }
}

async function fetchProductDetail(productId) {
  state.loading.detail = true;
  state.error = "";
  render();
  try {
    const response = await fetch(`${API_BASE}/api/v1/catalog/products/${productId}/`);
    if (!response.ok) throw new Error(`Product detail failed (${response.status})`);
    const payload = await response.json();
    state.productDetail = payload.product || null;
    state.relatedProducts = payload.related || [];
  } catch (error) {
    state.error = String(error);
    state.productDetail = null;
  } finally {
    state.loading.detail = false;
    render();
  }
}

async function runImageSearch(file) {
  state.loading.imageSearch = true;
  state.error = "";
  render();
  try {
    const formData = new FormData();
    formData.append("image", file);
    formData.append("top_k", "8");
    if (state.listFilters.category) formData.append("category", state.listFilters.category);
    const response = await fetch(`${API_BASE}/api/v1/search/image/`, {
      method: "POST",
      body: formData
    });
    if (!response.ok) throw new Error(`Image search failed (${response.status})`);
    const payload = await response.json();
    state.imageResults = payload.results || [];
  } catch (error) {
    state.error = String(error);
  } finally {
    state.loading.imageSearch = false;
    render();
  }
}

async function submitQuote(formData) {
  state.loading.quote = true;
  state.error = "";
  render();
  try {
    const payload = {
      product_id: state.productDetail?.id,
      name: formData.get("name"),
      email: formData.get("email"),
      phone: formData.get("phone"),
      company: formData.get("company"),
      message: formData.get("message")
    };
    const response = await fetch(`${API_BASE}/api/v1/quotes/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!response.ok) throw new Error(`Quote request failed (${response.status})`);
    alert("Quote request sent successfully.");
  } catch (error) {
    state.error = String(error);
  } finally {
    state.loading.quote = false;
    render();
  }
}

function bindEvents() {
  const headerSearchForm = document.querySelector("#header-search-form");
  const headerSearchInput = document.querySelector("#header-search-input");
  const modeButtons = document.querySelectorAll(".mode-btn");
  const heroSearchForm = document.querySelector("#hero-search-form");
  const heroSearchInput = document.querySelector("#hero-search-input");
  const categoryButtons = document.querySelectorAll(".chip[data-category]");
  const imageForm = document.querySelector("#image-search-form");
  const filterForm = document.querySelector("#catalog-filter-form");
  const sortBy = document.querySelector("#sort-by");
  const loadMoreBtn = document.querySelector("#load-more-btn");
  const addToCartButtons = document.querySelectorAll("[data-add-to-cart]");
  const detailAddButtons = document.querySelectorAll("[data-detail-add]");
  const openQuote = document.querySelector("#open-quote-btn");
  const openQuoteMobile = document.querySelector("#open-quote-btn-mobile");
  const closeQuote = document.querySelector("#close-quote-btn");
  const quoteDialog = document.querySelector("#quote-dialog");
  const quoteForm = document.querySelector("#quote-form");

  headerSearchForm?.addEventListener("submit", (event) => {
    event.preventDefault();
    navigateToCatalog({ q: headerSearchInput?.value || "", page: 1 });
  });

  modeButtons.forEach((button) => {
    button.addEventListener("click", () => {
      modeButtons.forEach((item) => item.classList.remove("active"));
      button.classList.add("active");
    });
  });

  heroSearchForm?.addEventListener("submit", (event) => {
    event.preventDefault();
    navigateToCatalog({ q: heroSearchInput?.value || "", page: 1 });
  });

  categoryButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const category = button.getAttribute("data-category") || "";
      if (route() === "catalog") {
        state.listFilters.category = category;
        state.listFilters.page = 1;
        updateCatalogHash();
      } else {
        navigateToCatalog({ category, page: 1 });
      }
    });
  });

  imageForm?.addEventListener("submit", (event) => {
    event.preventDefault();
    const file = imageForm.querySelector("input[name='image']")?.files?.[0];
    if (file) void runImageSearch(file);
  });

  filterForm?.addEventListener("submit", (event) => {
    event.preventDefault();
    const formData = new FormData(filterForm);
    state.listFilters = {
      ...state.listFilters,
      q: String(formData.get("q") || ""),
      min_price: String(formData.get("min_price") || ""),
      max_price: String(formData.get("max_price") || ""),
      in_stock: formData.get("in_stock") === "on",
      page: 1
    };
    updateCatalogHash();
  });

  sortBy?.addEventListener("change", () => {
    state.listFilters.sort_by = sortBy.value;
    state.listFilters.page = 1;
    updateCatalogHash();
  });

  loadMoreBtn?.addEventListener("click", () => {
    if (!state.pagination?.has_next || state.loading.products) return;
    state.listFilters.page += 1;
    void fetchProducts({ append: true });
  });

  addToCartButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const productId = Number(button.getAttribute("data-add-to-cart"));
      const product = [...state.products, ...state.recommendations, ...state.imageResults, ...state.relatedProducts].find(
        (item) => item.id === productId
      );
      if (product) addToCart(product);
    });
  });

  detailAddButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const productId = Number(button.getAttribute("data-detail-add"));
      if (state.productDetail && state.productDetail.id === productId) addToCart(state.productDetail);
    });
  });

  openQuote?.addEventListener("click", () => quoteDialog?.showModal());
  openQuoteMobile?.addEventListener("click", () => quoteDialog?.showModal());
  closeQuote?.addEventListener("click", () => quoteDialog?.close());

  quoteForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!quoteForm) return;
    const data = new FormData(quoteForm);
    await submitQuote(data);
    quoteDialog?.close();
  });
}

async function syncRouteData() {
  const current = route();
  if (!state.categories.length) await fetchCategories();

  if (current === "home") {
    if (!state.recommendations.length) await fetchRecommendations();
  } else if (current === "catalog") {
    state.listFilters = { ...state.listFilters, ...parseCatalogParams() };
    await fetchProducts();
  } else if (current === "product") {
    const productId = Number((window.location.hash || "").split("/")[2]);
    if (productId) await fetchProductDetail(productId);
  }
}

async function initialize() {
  render();
  await syncRouteData();
  render();
}

window.addEventListener("hashchange", () => {
  void syncRouteData();
});

void initialize();
