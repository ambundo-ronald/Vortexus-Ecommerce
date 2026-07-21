import fsSync from "node:fs";
import fs from "node:fs/promises";
import path from "node:path";

const DEFAULT_ORIGIN = "https://reesolmart.com";
const DEFAULT_IMAGE = "/Reesolmart logo.png";
const DEFAULT_TITLE = "Reesolmart | Just in time, buying";
const DEFAULT_DESCRIPTION = "Shop pumps, water treatment systems, filters, tanks, spares, and industrial supplies from Reesolmart.";

const rootDir = process.cwd();
const loadedEnv = loadEnvFiles(rootDir);
const distDir = path.join(rootDir, "dist");
const indexPath = path.join(distDir, "index.html");
const storefrontOrigin = cleanOrigin(envValue("VITE_STOREFRONT_ORIGIN", DEFAULT_ORIGIN));
const apiBaseUrl = cleanOrigin(envValue("VITE_SEO_API_BASE_URL", envValue("VITE_API_BASE_URL", "")));
const sitemapUrl = envValue("VITE_SEO_SITEMAP_URL", "");

const staticRoutes = [
  {
    path: "/",
    title: DEFAULT_TITLE,
    description: DEFAULT_DESCRIPTION,
    schemas: [
      organizationSchema(),
      websiteSchema()
    ]
  },
  {
    path: "/catalog",
    title: "Shop industrial supplies | Reesolmart",
    description: "Browse pumps, filters, tanks, water treatment systems, parts, and industrial supplies available on Reesolmart."
  },
  {
    path: "/offers",
    title: "Offers | Reesolmart",
    description: "Find current Reesolmart offers, discounts, and buying opportunities for industrial and water treatment supplies."
  },
  {
    path: "/orders/track",
    title: "Track your order | Reesolmart",
    description: "Track Reesolmart orders and delivery progress using your order details.",
    robots: "noindex, nofollow"
  }
];

async function main() {
  const shellHtml = await fs.readFile(indexPath, "utf8");
  const routes = new Map(staticRoutes.map((route) => [normalizePathname(route.path), route]));

  if (sitemapUrl) {
    const sitemapRoutes = await loadSitemapRoutes(sitemapUrl);
    for (const routePath of sitemapRoutes) {
      if (!routes.has(routePath)) routes.set(routePath, await routeSeo(routePath));
    }
  }

  for (const route of routes.values()) {
    await writeRouteHtml(shellHtml, route);
  }

  console.log(`SEO prerendered ${routes.size} route${routes.size === 1 ? "" : "s"}.`);
}

async function loadSitemapRoutes(url) {
  try {
    const response = await fetch(url, { headers: { Accept: "application/xml,text/xml,*/*" } });
    if (!response.ok) throw new Error(`Sitemap responded with ${response.status}`);
    const xml = await response.text();
    return [...xml.matchAll(/<loc>(.*?)<\/loc>/gi)]
      .map((match) => htmlDecode(match[1]))
      .map((value) => pathnameFromUrl(value))
      .filter(Boolean);
  } catch (error) {
    console.warn(`SEO prerender skipped dynamic sitemap routes: ${error.message}`);
    return [];
  }
}

async function routeSeo(routePath) {
  if (routePath.startsWith("/products/")) return productSeo(routePath);
  if (routePath.startsWith("/catalog/category/")) return categorySeo(routePath);
  if (routePath.startsWith("/catalog/brand/")) return brandSeo(routePath);
  if (routePath.startsWith("/offers/")) return offerSeo(routePath);
  if (routePath.startsWith("/catalog/ranges/")) return rangeSeo(routePath);
  return genericSeo(routePath);
}

async function productSeo(routePath) {
  const product = await fetchProduct(lastPathSegment(routePath));
  if (!product) return genericSeo(routePath);

  const title = productTitle(product);
  const brand = productBrand(product);
  const category = productCategory(product);
  const description = truncateText(
    stripHtml(product.description) ||
      [brand, category, "available from Reesolmart"].filter(Boolean).join(" "),
    155
  );
  const image = product.primary_image || product.thumbnail || product.images?.[0] || DEFAULT_IMAGE;
  const schemas = [
    productSchema(product, routePath, { title, brand, category, description, image }),
    breadcrumbSchema([
      { name: "Home", path: "/" },
      { name: "Shop", path: "/catalog" },
      ...productCategoryPath(product).map((item) => ({
        name: item.name || item.title || item.slug,
        path: item.slug ? `/catalog/category/${item.slug}` : "/catalog"
      })),
      { name: title, path: routePath }
    ])
  ];

  return {
    path: routePath,
    title: `${title} | Reesolmart`,
    description,
    image,
    type: "product",
    schemas
  };
}

async function fetchProduct(reference) {
  if (!apiBaseUrl || !reference) return null;
  try {
    const response = await fetch(`${apiBaseUrl}/catalog/products/${encodeURIComponent(reference)}/`, {
      headers: { Accept: "application/json" }
    });
    if (!response.ok) throw new Error(`Product responded with ${response.status}`);
    const payload = await response.json();
    return payload.product || payload;
  } catch (error) {
    console.warn(`SEO prerender skipped product ${reference}: ${error.message}`);
    return null;
  }
}

function categorySeo(routePath) {
  const name = titleFromSlug(lastPathSegment(routePath));
  return {
    path: routePath,
    title: `${name} | Reesolmart`,
    description: `Shop ${name.toLowerCase()} products and related industrial supplies from Reesolmart.`,
    schemas: breadcrumbSchema([
      { name: "Home", path: "/" },
      { name: "Shop", path: "/catalog" },
      { name, path: routePath }
    ])
  };
}

function brandSeo(routePath) {
  const name = titleFromSlug(lastPathSegment(routePath));
  return {
    path: routePath,
    title: `${name} products | Reesolmart`,
    description: `Browse ${name} products, spares, and industrial supplies available through Reesolmart.`
  };
}

function offerSeo(routePath) {
  const name = titleFromSlug(lastPathSegment(routePath));
  return {
    path: routePath,
    title: `${name} offer | Reesolmart`,
    description: `View the ${name} offer on Reesolmart and shop eligible industrial products.`
  };
}

function rangeSeo(routePath) {
  const name = titleFromSlug(lastPathSegment(routePath));
  return {
    path: routePath,
    title: `${name} range | Reesolmart`,
    description: `Browse the ${name} product range on Reesolmart.`
  };
}

function genericSeo(routePath) {
  const name = routePath === "/" ? "Reesolmart" : titleFromSlug(lastPathSegment(routePath));
  return {
    path: routePath,
    title: `${name} | Reesolmart`,
    description: DEFAULT_DESCRIPTION
  };
}

async function writeRouteHtml(shellHtml, route) {
  const html = injectSeo(shellHtml, route);
  const routePath = normalizePathname(route.path);

  if (routePath === "/") {
    await fs.writeFile(indexPath, html);
    return;
  }

  const targetDir = safeRouteDir(routePath);
  await fs.mkdir(targetDir, { recursive: true });
  await fs.writeFile(path.join(targetDir, "index.html"), html);
}

function injectSeo(html, route) {
  const canonical = absoluteUrl(route.path);
  const image = absoluteUrl(route.image || DEFAULT_IMAGE);
  const title = route.title || DEFAULT_TITLE;
  const description = route.description || DEFAULT_DESCRIPTION;
  const type = route.type || "website";
  const schemas = Array.isArray(route.schemas) ? route.schemas.filter(Boolean) : [route.schemas].filter(Boolean);
  const block = [
    '<meta data-reesolmart-prerender="true" name="description" content="' + escapeAttr(description) + '" />',
    route.robots ? '<meta data-reesolmart-prerender="true" name="robots" content="' + escapeAttr(route.robots) + '" />' : "",
    '<link data-reesolmart-prerender="true" rel="canonical" href="' + escapeAttr(canonical) + '" />',
    '<meta data-reesolmart-prerender="true" property="og:title" content="' + escapeAttr(title) + '" />',
    '<meta data-reesolmart-prerender="true" property="og:description" content="' + escapeAttr(description) + '" />',
    '<meta data-reesolmart-prerender="true" property="og:type" content="' + escapeAttr(type) + '" />',
    '<meta data-reesolmart-prerender="true" property="og:url" content="' + escapeAttr(canonical) + '" />',
    '<meta data-reesolmart-prerender="true" property="og:image" content="' + escapeAttr(image) + '" />',
    '<meta data-reesolmart-prerender="true" name="twitter:card" content="summary_large_image" />',
    '<meta data-reesolmart-prerender="true" name="twitter:title" content="' + escapeAttr(title) + '" />',
    '<meta data-reesolmart-prerender="true" name="twitter:description" content="' + escapeAttr(description) + '" />',
    '<meta data-reesolmart-prerender="true" name="twitter:image" content="' + escapeAttr(image) + '" />',
    ...schemas.map((schema) => (
      '<script data-reesolmart-prerender="true" type="application/ld+json">' +
      JSON.stringify(schema).replace(/</g, "\\u003c") +
      '</script>'
    ))
  ].filter(Boolean).join("\n    ");

  return html
    .replace(/<title>.*?<\/title>/is, `<title>${escapeHtml(title)}</title>`)
    .replace(/<meta\s+name=["']description["'][^>]*>\s*/i, "")
    .replace(/\s*<script\b[^>]*data-reesolmart-prerender=["']true["'][^>]*>[\s\S]*?<\/script>/gi, "")
    .replace(/\s*<(?:meta|link)\b[^>]*data-reesolmart-prerender=["']true["'][^>]*\/?>/gi, "")
    .replace("</head>", `    ${block}\n  </head>`);
}

function productSchema(product, routePath, { title, brand, category, description, image }) {
  const price = numericValue(product.price || product.price_excl_tax || product.unit_price || product.regional_price?.value);
  const currency = product.currency || product.price_currency || product.regional_price?.currency || "KES";
  const schema = {
    "@context": "https://schema.org",
    "@type": "Product",
    name: title,
    description,
    image: absoluteUrl(image),
    sku: product.sku || product.upc || product.code || undefined,
    brand: brand ? { "@type": "Brand", name: brand } : undefined,
    category: category || undefined,
    url: absoluteUrl(routePath)
  };

  if (price > 0) {
    schema.offers = {
      "@type": "Offer",
      price,
      priceCurrency: currency,
      availability: productIsAvailable(product) ? "https://schema.org/InStock" : "https://schema.org/OutOfStock",
      url: absoluteUrl(routePath)
    };
  }

  return removeEmpty(schema);
}

function breadcrumbSchema(items) {
  return {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: items.filter(Boolean).map((item, index) => ({
      "@type": "ListItem",
      position: index + 1,
      name: item.name,
      item: absoluteUrl(item.path)
    }))
  };
}

function organizationSchema() {
  return {
    "@context": "https://schema.org",
    "@type": "Organization",
    name: "Reesolmart",
    url: storefrontOrigin,
    logo: absoluteUrl(DEFAULT_IMAGE),
    slogan: "Just in time, buying"
  };
}

function websiteSchema() {
  return {
    "@context": "https://schema.org",
    "@type": "WebSite",
    name: "Reesolmart",
    url: storefrontOrigin,
    potentialAction: {
      "@type": "SearchAction",
      target: `${storefrontOrigin}/search?q={search_term_string}`,
      "query-input": "required name=search_term_string"
    }
  };
}

function productTitle(product) {
  return product.title || product.name || product.product_title || "Product";
}

function productBrand(product) {
  return product.brand || product.brand_name || product.manufacturer || "";
}

function productCategory(product) {
  const category = product.category || product.categories?.[0];
  if (typeof category === "string") return category;
  return category?.name || category?.title || "";
}

function productCategoryPath(product) {
  const source = product.category_path || product.categories?.[0]?.path;
  if (Array.isArray(source) && source.length) return source;
  const category = product.categories?.[0] || product.category;
  if (!category) return [];
  if (typeof category === "string") return [{ name: category, slug: slugifySegment(category) }];
  return [category];
}

function productIsAvailable(product) {
  if (typeof product.is_available === "boolean") return product.is_available;
  if (typeof product.availability?.is_available === "boolean") return product.availability.is_available;
  const stock = numericValue(product.stock || product.stock_count || product.num_in_stock || product.availability?.num_available);
  return stock > 0;
}

function safeRouteDir(routePath) {
  const segments = routePath.split("/").filter(Boolean).map((segment) => slugifySegment(segment) || "page");
  return path.join(distDir, ...segments);
}

function pathnameFromUrl(value) {
  try {
    const url = new URL(value);
    if (url.origin !== storefrontOrigin) return "";
    return normalizePathname(url.pathname);
  } catch {
    return normalizePathname(value);
  }
}

function absoluteUrl(value = "/") {
  const raw = String(value || "/");
  if (/^https?:\/\//i.test(raw)) return raw;
  return new URL(raw.startsWith("/") ? raw : `/${raw}`, storefrontOrigin).toString();
}

function normalizePathname(value = "/") {
  const pathname = String(value || "/").split("?")[0].split("#")[0];
  const normalized = pathname.startsWith("/") ? pathname : `/${pathname}`;
  return normalized.replace(/\/{2,}/g, "/").replace(/\/$/, "") || "/";
}

function lastPathSegment(value = "") {
  return decodeURIComponent(normalizePathname(value).split("/").filter(Boolean).pop() || "");
}

function titleFromSlug(value = "") {
  return String(value || "Page")
    .replace(/[-_]+/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function slugifySegment(value = "") {
  return String(value || "")
    .toLowerCase()
    .replace(/&/g, " and ")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function stripHtml(value = "") {
  return String(value || "").replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim();
}

function truncateText(value = "", maxLength = 155) {
  const text = String(value || "").replace(/\s+/g, " ").trim();
  if (text.length <= maxLength) return text;
  return `${text.slice(0, maxLength - 1).trim()}...`;
}

function numericValue(value) {
  const number = Number(String(value ?? "").replace(/[^\d.-]/g, ""));
  return Number.isFinite(number) ? number : 0;
}

function cleanOrigin(value = "") {
  return String(value || "").replace(/\/+$/, "");
}

function htmlDecode(value = "") {
  return String(value)
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'");
}

function escapeHtml(value = "") {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function escapeAttr(value = "") {
  return escapeHtml(value).replace(/"/g, "&quot;");
}

function removeEmpty(value) {
  if (Array.isArray(value)) return value.map(removeEmpty).filter((item) => item !== undefined);
  if (!value || typeof value !== "object") return value;
  return Object.fromEntries(
    Object.entries(value)
      .map(([key, entry]) => [key, removeEmpty(entry)])
      .filter(([, entry]) => entry !== undefined && entry !== "" && !(Array.isArray(entry) && !entry.length))
  );
}

function envValue(name, fallback = "") {
  return process.env[name] ?? loadedEnv[name] ?? fallback;
}

function loadEnvFiles(directory) {
  const mode = process.env.MODE || process.env.NODE_ENV || "production";
  const files = [".env", ".env.local", `.env.${mode}`, `.env.${mode}.local`];
  const values = {};

  for (const file of files) {
    const filePath = path.join(directory, file);
    if (!fsSync.existsSync(filePath)) continue;
    const contents = fsSync.readFileSync(filePath, "utf8");
    for (const line of contents.split(/\r?\n/)) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith("#")) continue;
      const separator = trimmed.indexOf("=");
      if (separator === -1) continue;
      const key = trimmed.slice(0, separator).trim();
      const rawValue = trimmed.slice(separator + 1).trim();
      values[key] = unquoteEnvValue(rawValue);
    }
  }

  return values;
}

function unquoteEnvValue(value = "") {
  if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
    return value.slice(1, -1);
  }
  return value;
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
