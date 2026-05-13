import { formatCurrency, storefrontCurrency } from "./currency";

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
  const desiredCurrency = storefrontCurrency();
  const selected = selectRegionalPrice(product, desiredCurrency);
  const numericValue = Number(selected.value);
  const previous = selectPreviousRegionalPrice(product, selected.currency);
  const previousValue = Number(previous.value);
  const hasPreviousPrice = Number.isFinite(previousValue) && previousValue > numericValue;
  const discountPercent = hasPreviousPrice ? Math.round(((previousValue - numericValue) / previousValue) * 100) : 0;

  if (!Number.isFinite(numericValue) || numericValue <= 0) {
    return {
      label: "",
      sublabel: "",
      currency: selected.currency,
      previousLabel: "",
      discountLabel: "",
      isQuote: true
    };
  }

  return {
    label: formatCurrency(numericValue, selected.currency),
    sublabel: "",
    currency: selected.currency,
    previousLabel: hasPreviousPrice ? formatCurrency(previousValue, selected.currency) : "",
    discountLabel: hasPreviousPrice ? `-${discountPercent}%` : "",
    isQuote: false
  };
}

function selectRegionalPrice(product = {}, desiredCurrency = "KES") {
  const priceOptions = [
    { value: product.base_price, currency: product.base_currency },
    { value: product.price, currency: product.currency },
    { value: product.price_excl_tax, currency: product.currency },
    { value: product.price_incl_tax, currency: product.currency }
  ].filter((option) => option.value !== null && option.value !== undefined && option.value !== "");

  const exact = priceOptions.find((option) => sameCurrency(option.currency, desiredCurrency));
  if (exact) {
    return {
      value: exact.value,
      currency: desiredCurrency
    };
  }

  const fallback = priceOptions[0] || {};
  return {
    value: fallback.value,
    currency: fallback.currency || desiredCurrency
  };
}

function sameCurrency(left, right) {
  return String(left || "").toUpperCase() === String(right || "").toUpperCase();
}

function selectPreviousRegionalPrice(product = {}, selectedCurrency = "KES") {
  const previousOptions = [
    { value: product.base_previous_price, currency: product.base_previous_currency || product.base_currency },
    { value: product.previous_base_price, currency: product.previous_base_currency || product.base_currency },
    { value: product.base_old_price, currency: product.base_currency },
    { value: product.old_base_price, currency: product.base_currency },
    { value: product.previous_price, currency: product.previous_currency || product.currency },
    { value: product.old_price, currency: product.currency },
    { value: product.was_price, currency: product.currency },
    { value: product.original_price, currency: product.currency },
    { value: product.price_before_discount, currency: product.currency },
    { value: product.retail_price, currency: product.currency }
  ].filter((option) => option.value !== null && option.value !== undefined && option.value !== "");

  const exact = previousOptions.find((option) => !option.currency || sameCurrency(option.currency, selectedCurrency));
  if (exact) {
    return {
      value: exact.value,
      currency: selectedCurrency
    };
  }

  return {};
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
