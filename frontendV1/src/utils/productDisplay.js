import { formatCurrency } from "./currency";

export function productInitials(title = "") {
  const words = String(title)
    .replace(/[^\p{L}\p{N}\s-]/gu, " ")
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 3);

  if (!words.length) return "VX";

  return words
    .map((word) => word[0])
    .join("")
    .toUpperCase()
    .slice(0, 3);
}

export function productPrice(product) {
  const preferredValue = product.base_price ?? product.price;
  const preferredCurrency = product.base_currency || product.currency || "KES";
  const numericValue = Number(preferredValue);

  if (!Number.isFinite(numericValue) || numericValue <= 0) {
    return {
      label: "",
      sublabel: "",
      isQuote: true
    };
  }

  return {
    label: formatCurrency(numericValue, preferredCurrency),
    sublabel: product.currency && product.currency !== preferredCurrency ? formatCurrency(product.price, product.currency) : "",
    isQuote: false
  };
}

export function stockTone(product) {
  if (product.in_stock) return { tone: "success", label: "In stock" };
  return { tone: "warning", label: "Check availability" };
}
