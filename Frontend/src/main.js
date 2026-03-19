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
    basket: {
        lines: [],
        line_count: 0,
        item_count: 0,
        totals: { subtotal: 0, currency: "USD" },
        shipping_required: false,
        is_empty: true
    },
    checkout: {
        countries: [],
        address: null,
        shipping_required: false,
        methods: [],
        selected_method: null,
        ready_for_checkout: false,
        missing: [],
        taxes: { known: false, country_code: "", rate: null, merchandise_tax: 0, shipping_tax: 0, total_tax: 0 },
        totals: { subtotal: 0, shipping: 0, tax: 0, order_total: 0, currency: "USD" }
    },
    csrfToken: "",
    loading: {
        categories: false,
        products: false,
        detail: false,
        recommendations: false,
        imageSearch: false,
        quote: false,
        checkout: false,
        cartAction: false,
        shippingSave: false
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
    if (hash.startsWith("#/checkout")) return "checkout";
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

function countCartItems() {
    return state.basket.item_count || 0;
}

function cartTotal() {
    if (state.checkout?.selected_method || route() === "checkout") {
        return state.checkout.totals.order_total || 0;
    }
    return state.basket.totals.subtotal || 0;
}

function activeCurrency() {
    return state.checkout.totals.currency || state.basket.totals.currency || "USD";
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

function apiErrorMessage(payload, fallback) {
    if (!payload) return fallback;
    if (payload.error?.detail) return payload.error.detail;
    if (payload.detail) return payload.detail;
    return fallback;
}

async function ensureCsrfToken() {
    if (state.csrfToken) return state.csrfToken;
    const response = await fetch(`${API_BASE}/api/v1/account/csrf/`, {
        credentials: "include"
    });
    if (!response.ok) {
        throw new Error(`CSRF bootstrap failed (${response.status})`);
    }
    const payload = await response.json();
    state.csrfToken = payload.csrf_token || "";
    return state.csrfToken;
}

async function apiRequest(path, options = {}) {
    const method = (options.method || "GET").toUpperCase();
    const headers = new Headers(options.headers || {});
    const isFormData = options.body instanceof FormData;

    if (!["GET", "HEAD", "OPTIONS"].includes(method)) {
        await ensureCsrfToken();
        if (state.csrfToken) headers.set("X-CSRFToken", state.csrfToken);
    }

    if (!isFormData && options.body && !headers.has("Content-Type")) {
        headers.set("Content-Type", "application/json");
    }

    const response = await fetch(`${API_BASE}${path}`, {
        ...options,
        method,
        credentials: "include",
        headers
    });

    const contentType = response.headers.get("content-type") || "";
    let payload = null;

    if (contentType.includes("application/json")) {
        payload = await response.json();
    } else if (!response.ok) {
        payload = { detail: await response.text() };
    }

    if (!response.ok) {
        throw new Error(apiErrorMessage(payload, `Request failed (${response.status})`));
    }

    if (payload?.csrf_token) {
        state.csrfToken = payload.csrf_token;
    }

    return payload;
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
          <button class="btn-mini" data-add-to-cart="${product.id}">${state.loading.cartAction ? "..." : "Add"}</button>
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
        <a class="cart-pill" href="#/checkout">Cart ${countCartItems()}</a>
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
      ${state.recommendations.length
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
      ${state.imageResults.length
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

          ${state.products.length
            ? `<div class="product-grid">${state.products.map(productCardHtml).join("")}</div>`
            : `<p class="empty">No products found with these filters.</p>`
        }

          ${state.pagination?.has_next
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
      <a class="back-link" href="#/catalog">&lt; Back to catalog</a>
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
          ${product.categories?.length
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
        ${state.relatedProducts.length
            ? `<div class="product-grid">${state.relatedProducts.map(productCardHtml).join("")}</div>`
            : `<p class="empty">No related products available.</p>`
        }
      </section>
    </section>

    <div class="sticky-actions">
      <span>${toCurrency(product.price, product.currency)}</span>
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

function basketLineHtml(line) {
    return `
    <article class="basket-line">
      <a href="#/product/${line.product.id}" class="basket-thumb">
        <img src="${imageUrl(line.product.thumbnail)}" alt="${line.product.title}" loading="lazy" />
      </a>
      <div class="basket-line-body">
        <h3><a href="#/product/${line.product.id}">${line.product.title}</a></h3>
        <p class="sku">${line.product.sku || line.line_reference}</p>
        <p class="stock ${line.availability.is_available ? "ok" : "warn"}">${line.availability.message || (line.availability.is_available ? "Ready for checkout" : "Availability check required")}</p>
      </div>
      <div class="basket-line-actions">
        <p class="price">${toCurrency(line.line_total, line.currency)}</p>
        <div class="qty-control">
          <button type="button" class="qty-btn" data-line-update="${line.id}" data-quantity="${Math.max(0, line.quantity - 1)}">-</button>
          <span>${line.quantity}</span>
          <button type="button" class="qty-btn" data-line-update="${line.id}" data-quantity="${line.quantity + 1}">+</button>
        </div>
        <button type="button" class="text-btn" data-remove-line="${line.id}">Remove</button>
      </div>
    </article>
  `;
}

function shippingMethodHtml(method) {
    return `
    <button type="button" class="shipping-method ${method.selected ? "selected" : ""}" data-select-shipping="${method.code}">
      <span>
        <strong>${method.name}</strong>
        <small>${method.description}</small>
      </span>
      <span class="shipping-charge">${toCurrency(method.charge, method.currency)}</span>
    </button>
  `;
}

function checkoutViewHtml() {
    const lines = state.basket.lines || [];
    const address = state.checkout.address || {};
    const countries = state.checkout.countries || [];

    return `
    <section class="panel checkout-shell">
      <div class="panel-head">
        <h2>Checkout</h2>
        <p>${state.basket.item_count || 0} items in basket</p>
      </div>

      <div class="checkout-grid">
        <div class="checkout-main">
          <section class="checkout-section">
            <div class="section-head">
              <h3>Basket</h3>
              <a href="#/catalog" class="text-link">Add more products</a>
            </div>
            ${lines.length
            ? `<div class="basket-lines">${lines.map(basketLineHtml).join("")}</div>`
            : `<p class="empty">Your basket is empty. Add pumps, accessories, or treatment components to continue.</p>`
        }
          </section>

          <section class="checkout-section">
            <div class="section-head">
              <h3>Delivery Address</h3>
              <p class="subtle">Used to determine available shipping options.</p>
            </div>
            <form id="shipping-address-form" class="shipping-form">
              <div class="form-grid">
                <label>
                  First name
                  <input type="text" name="first_name" value="${address.first_name || ""}" required />
                </label>
                <label>
                  Last name
                  <input type="text" name="last_name" value="${address.last_name || ""}" required />
                </label>
                <label>
                  Phone
                  <input type="text" name="phone_number" value="${address.phone_number || ""}" placeholder="+254..." />
                </label>
                <label>
                  Country
                  <select name="country_code" required>
                    <option value="">Select country</option>
                    ${countries
            .map(
                (country) =>
                    `<option value="${country.code}" ${country.code === (address.country_code || "KE") ? "selected" : ""}>${country.name}</option>`
            )
            .join("")}
                  </select>
                </label>
                <label class="full-span">
                  Address line 1
                  <input type="text" name="line1" value="${address.line1 || ""}" required />
                </label>
                <label class="full-span">
                  Address line 2
                  <input type="text" name="line2" value="${address.line2 || ""}" />
                </label>
                <label>
                  Area / site
                  <input type="text" name="line3" value="${address.line3 || ""}" />
                </label>
                <label>
                  City
                  <input type="text" name="line4" value="${address.line4 || ""}" required />
                </label>
                <label>
                  State / county
                  <input type="text" name="state" value="${address.state || ""}" />
                </label>
                <label>
                  Postcode
                  <input type="text" name="postcode" value="${address.postcode || ""}" />
                </label>
                <label class="full-span">
                  Delivery notes
                  <textarea name="notes" rows="3" placeholder="Site contact, gate instructions, unloading requirements...">${address.notes || ""}</textarea>
                </label>
              </div>
              <button type="submit" class="primary-btn">${state.loading.shippingSave ? "Saving..." : "Save Delivery Address"}</button>
            </form>
          </section>

          <section class="checkout-section">
            <div class="section-head">
              <h3>Shipping Method</h3>
              <p class="subtle">Choose the delivery mode for this order.</p>
            </div>
            ${state.checkout.methods.length
            ? `<div class="shipping-methods">${state.checkout.methods.map(shippingMethodHtml).join("")}</div>`
            : `<p class="empty">Add products to the basket to see shipping methods.</p>`
        }
          </section>
        </div>

        <aside class="checkout-side">
          <section class="checkout-section order-summary">
            <h3>Order Summary</h3>
            <div class="summary-row">
              <span>Subtotal</span>
              <strong>${toCurrency(state.checkout.totals.subtotal, state.checkout.totals.currency)}</strong>
            </div>
            <div class="summary-row">
              <span>Shipping</span>
              <strong>${toCurrency(state.checkout.totals.shipping, state.checkout.totals.currency)}</strong>
            </div>
            <div class="summary-row">
              <span>Tax</span>
              <strong>${state.checkout.taxes?.known
            ? toCurrency(state.checkout.totals.tax, state.checkout.totals.currency)
            : "Pending address"
        }</strong>
            </div>
            <div class="summary-row total-row">
              <span>Order total</span>
              <strong>${toCurrency(state.checkout.totals.order_total, state.checkout.totals.currency)}</strong>
            </div>
            <div class="checkout-status ${state.checkout.ready_for_checkout ? "ready" : "pending"}">
              ${state.checkout.ready_for_checkout
            ? "Basket, address, and shipping method are captured."
            : `Missing: ${state.checkout.missing.join(", ") || "basket"}`
        }
            </div>
            <button type="button" class="primary-btn" ${state.checkout.ready_for_checkout ? "" : "disabled"}>Proceed to payment</button>
          </section>
        </aside>
      </div>
    </section>
  `;
}

function footerHtml() {
    return `
    <footer class="footer">
      <div>
        <strong>Estimated Total:</strong> ${toCurrency(cartTotal(), activeCurrency())}
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
    else if (current === "checkout") content = checkoutViewHtml();
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

function syncCheckoutState(payload) {
    if (payload?.basket) state.basket = payload.basket;
    if (payload?.shipping) state.checkout = payload.shipping;
}

async function fetchCategories() {
    state.loading.categories = true;
    try {
        const payload = await apiRequest("/api/v1/catalog/categories/");
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
        const payload = await apiRequest(`/api/v1/catalog/products/?${params.toString()}`);
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
        const payload = await apiRequest("/api/v1/recommendations/?limit=8");
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
        const payload = await apiRequest(`/api/v1/catalog/products/${productId}/`);
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

async function fetchCheckoutState({ renderFirst = false } = {}) {
    state.loading.checkout = true;
    if (renderFirst) render();
    try {
        const payload = await apiRequest("/api/v1/checkout/shipping/");
        syncCheckoutState(payload);
    } catch (error) {
        state.error = String(error);
    } finally {
        state.loading.checkout = false;
        render();
    }
}

async function addProductToBasket(productId) {
    state.loading.cartAction = true;
    state.error = "";
    render();
    try {
        const payload = await apiRequest("/api/v1/checkout/basket/items/", {
            method: "POST",
            body: JSON.stringify({ product_id: productId, quantity: 1 })
        });
        syncCheckoutState(payload);
    } catch (error) {
        state.error = String(error);
    } finally {
        state.loading.cartAction = false;
        render();
    }
}
async function updateBasketLine(lineId, quantity) {
    state.loading.cartAction = true;
    state.error = "";
    render();
    try {
        const payload = await apiRequest(`/api/v1/checkout/basket/items/${lineId}/`, {
            method: "PATCH",
            body: JSON.stringify({ quantity })
        });
        syncCheckoutState(payload);
    } catch (error) {
        state.error = String(error);
    } finally {
        state.loading.cartAction = false;
        render();
    }
}

async function removeBasketLine(lineId) {
    state.loading.cartAction = true;
    state.error = "";
    render();
    try {
        const payload = await apiRequest(`/api/v1/checkout/basket/items/${lineId}/`, {
            method: "DELETE"
        });
        syncCheckoutState(payload);
    } catch (error) {
        state.error = String(error);
    } finally {
        state.loading.cartAction = false;
        render();
    }
}

async function saveShippingAddress(formData) {
    state.loading.shippingSave = true;
    state.error = "";
    render();
    try {
        const payload = await apiRequest("/api/v1/checkout/shipping/address/", {
            method: "PUT",
            body: JSON.stringify({
                first_name: String(formData.get("first_name") || ""),
                last_name: String(formData.get("last_name") || ""),
                line1: String(formData.get("line1") || ""),
                line2: String(formData.get("line2") || ""),
                line3: String(formData.get("line3") || ""),
                line4: String(formData.get("line4") || ""),
                state: String(formData.get("state") || ""),
                postcode: String(formData.get("postcode") || ""),
                country_code: String(formData.get("country_code") || ""),
                phone_number: String(formData.get("phone_number") || ""),
                notes: String(formData.get("notes") || "")
            })
        });
        syncCheckoutState(payload);
    } catch (error) {
        state.error = String(error);
    } finally {
        state.loading.shippingSave = false;
        render();
    }
}

async function selectShippingMethod(methodCode) {
    state.loading.shippingSave = true;
    state.error = "";
    render();
    try {
        const payload = await apiRequest("/api/v1/checkout/shipping/select/", {
            method: "POST",
            body: JSON.stringify({ method_code: methodCode })
        });
        syncCheckoutState(payload);
    } catch (error) {
        state.error = String(error);
    } finally {
        state.loading.shippingSave = false;
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
        const payload = await apiRequest("/api/v1/search/image/", {
            method: "POST",
            body: formData
        });
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
        await apiRequest("/api/v1/quotes/", {
            method: "POST",
            body: JSON.stringify({
                product_id: state.productDetail?.id,
                name: formData.get("name"),
                email: formData.get("email"),
                phone: formData.get("phone"),
                company: formData.get("company"),
                message: formData.get("message")
            })
        });
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
    const lineUpdateButtons = document.querySelectorAll("[data-line-update]");
    const removeLineButtons = document.querySelectorAll("[data-remove-line]");
    const shippingForm = document.querySelector("#shipping-address-form");
    const shippingButtons = document.querySelectorAll("[data-select-shipping]");

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
            if (productId) void addProductToBasket(productId);
        });
    });

    detailAddButtons.forEach((button) => {
        button.addEventListener("click", () => {
            const productId = Number(button.getAttribute("data-detail-add"));
            if (productId) void addProductToBasket(productId);
        });
    });

    lineUpdateButtons.forEach((button) => {
        button.addEventListener("click", () => {
            const lineId = Number(button.getAttribute("data-line-update"));
            const quantity = Number(button.getAttribute("data-quantity"));
            if (lineId >= 0 && quantity >= 0) void updateBasketLine(lineId, quantity);
        });
    });

    removeLineButtons.forEach((button) => {
        button.addEventListener("click", () => {
            const lineId = Number(button.getAttribute("data-remove-line"));
            if (lineId) void removeBasketLine(lineId);
        });
    });

    shippingForm?.addEventListener("submit", (event) => {
        event.preventDefault();
        void saveShippingAddress(new FormData(shippingForm));
    });

    shippingButtons.forEach((button) => {
        button.addEventListener("click", () => {
            const methodCode = button.getAttribute("data-select-shipping");
            if (methodCode) void selectShippingMethod(methodCode);
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

    if (!state.csrfToken) {
        await ensureCsrfToken();
    }
    if (!state.categories.length) {
        await fetchCategories();
    }
    await fetchCheckoutState();

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
