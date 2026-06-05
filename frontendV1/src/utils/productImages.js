import { mediaUrl } from "./media";

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
  return mediaUrl(first || "");
}

export function productImageList(product = {}) {
  const images = [];
  const primary = productImageUrl(product);
  if (primary) images.push(primary);

  if (Array.isArray(product.images)) {
    for (const image of product.images) {
      const url = mediaUrl(imageCandidate(image));
      if (url && !images.includes(url)) images.push(url);
    }
  }

  return images;
}
