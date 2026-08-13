import { mediaUrl } from "./media";
import { productBrand, productCategory, productTitle } from "./productDisplay";

function imageCandidate(value) {
  if (!value) return "";
  if (typeof value === "string") return value;
  return value.src || value.url || value.original || value.original_url || value.image || value.image_url || value.thumbnail || "";
}

export function productImageUrl(product = {}) {
  const candidates = [
    product.thumbnail,
    product.primary_image,
    product.primaryImage,
    product.image_url,
    product.imageUrl,
    product.image,
    product.src,
    product.original_url,
    product.url,
    product.product?.thumbnail,
    product.product?.primary_image,
    product.product?.image_url,
    product.product?.image,
    product.product?.src
  ];

  if (Array.isArray(product.images)) {
    candidates.push(...product.images.map(imageCandidate));
  }

  const first = candidates.map(imageCandidate).find(Boolean);
  return withProductVersion(mediaUrl(first || ""), product);
}

export function productImageList(product = {}) {
  const images = [];
  const primary = productImageUrl(product);
  if (primary) images.push(primary);

  if (Array.isArray(product.images)) {
    for (const image of product.images) {
      const url = withProductVersion(mediaUrl(imageCandidate(image)), product);
      if (url && !images.includes(url)) images.push(url);
    }
  }

  return images;
}

export function productImageAlt(product = {}, fallback = "Product image") {
  const title = productTitle(product, "").trim();
  const brand = productBrand(product, "").trim();
  const category = productCategory(product, "").trim();
  const parts = [title, brand, category].filter(Boolean);
  if (!parts.length) return fallback;
  return `${parts.join(" - ")} product image`;
}

function withProductVersion(url, product = {}) {
  if (!url || /^(data|blob):/i.test(url)) return url;
  const version =
    product.updated_at ||
    product.date_updated ||
    product.updatedAt ||
    product.product?.updated_at ||
    product.product?.date_updated ||
    product.product?.updatedAt;
  if (!version || /[?&]v=/.test(url)) return url;
  const separator = url.includes("?") ? "&" : "?";
  return `${url}${separator}v=${encodeURIComponent(String(version))}`;
}
