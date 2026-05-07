export const PRODUCT_PLACEHOLDER_IMAGES = [
  "/images/Placeholder.jpg",
  "/images/back%20view.png",
  "/images/left%20view%20palce%20holder.jpg",
  "/images/right%20view%20placeholder.jpg"
];

export function productPlaceholderImage(index = 0) {
  return PRODUCT_PLACEHOLDER_IMAGES[index] || PRODUCT_PLACEHOLDER_IMAGES[0];
}
