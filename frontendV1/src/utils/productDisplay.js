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
  const stockCount = Number(product?.stock_count ?? product?.num_in_stock ?? product?.stock ?? 0);
  if (stockCount > 0 || product?.in_stock) {
    return {
      tone: "success",
      label: stockCount > 0 ? `In stock: ${stockCount}` : "In stock",
      count: stockCount,
      isAvailable: true
    };
  }
  return {
    tone: "warning",
    label: "Sold out",
    count: 0,
    isAvailable: false
  };
}
