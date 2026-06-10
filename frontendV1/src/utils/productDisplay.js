import { formatCurrency, storefrontCurrency } from "./currency";

export function productId(product = {}) {
  return product.id || product.product_id || product.productId || product.product?.id || product.product?.product_id || "";
}

export function productTitle(product = {}, fallback = "Product") {
  return (
    product.title ||
    product.name ||
    product.product_title ||
    product.productTitle ||
    product.line_title ||
    product.product?.title ||
    product.product?.name ||
    fallback
  );
}

export function productSku(product = {}, fallback = "") {
  return (
    product.sku ||
    product.upc ||
    product.code ||
    product.partner_sku ||
    product.line_reference ||
    product.product?.sku ||
    product.product?.upc ||
    product.product?.code ||
    fallback
  );
}

export function productBrand(product = {}, fallback = "") {
  return (
    product.brand ||
    product.brand_name ||
    product.manufacturer ||
    product.product?.brand ||
    product.product?.brand_name ||
    product.product?.manufacturer ||
    fallback
  );
}

export function productCategory(product = {}, fallback = "") {
  const category =
    product.category ||
    product.categories?.[0] ||
    product.product?.category ||
    product.product?.categories?.[0];

  if (typeof category === "string") return category || fallback;
  return category?.name || category?.title || fallback;
}

export function productRating(product = {}) {
  const rating = Number(
    firstValue(
      product.rating,
      product.average_rating,
      product.average_review_score,
      product.review_score,
      product.product?.rating,
      product.product?.average_rating,
      product.product?.average_review_score,
      product.product?.review_score
    ) ?? 0
  );
  const reviewCount = Number(
    firstValue(
      product.review_count,
      product.reviews_count,
      product.num_reviews,
      product.product?.review_count,
      product.product?.reviews_count,
      product.product?.num_reviews
    ) ?? 0
  );

  return {
    rating: Number.isFinite(rating) ? rating : 0,
    reviewCount: Number.isFinite(reviewCount) ? reviewCount : 0,
    hasRating: Number.isFinite(rating) && rating > 0
  };
}

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
  const source = product || {};
  const desiredCurrency = storefrontCurrency();
  const selected = selectRegionalPrice(source, desiredCurrency);
  const numericValue = Number(selected.value);
  const previous = selectPreviousRegionalPrice(source, selected.currency);
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
    { value: product.display_price, currency: product.display_currency || product.currency },
    { value: product.unit_price, currency: product.currency },
    { value: product.line_total, currency: product.currency },
    { value: product.line_price_incl_tax, currency: product.currency },
    { value: product.line_price_excl_tax, currency: product.currency },
    { value: product.total_incl_tax, currency: product.currency },
    { value: product.price_excl_tax, currency: product.currency },
    { value: product.price_incl_tax, currency: product.currency },
    { value: product.product?.base_price, currency: product.product?.base_currency },
    { value: product.product?.price, currency: product.product?.currency },
    { value: product.product?.price_excl_tax, currency: product.product?.currency },
    { value: product.product?.price_incl_tax, currency: product.product?.currency }
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
    { value: product.retail_price, currency: product.currency },
    { value: product.product?.base_previous_price, currency: product.product?.base_previous_currency || product.product?.base_currency },
    { value: product.product?.previous_price, currency: product.product?.previous_currency || product.product?.currency },
    { value: product.product?.old_price, currency: product.product?.currency },
    { value: product.product?.was_price, currency: product.product?.currency },
    { value: product.product?.original_price, currency: product.product?.currency }
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
  const rawStockCount = firstValue(
    product?.stock_count,
    product?.num_in_stock,
    product?.stock,
    product?.available_quantity,
    product?.availability?.num_available,
    product?.availability?.num_in_stock,
    product?.availability?.stock,
    product?.product?.stock_count,
    product?.product?.num_in_stock,
    product?.product?.stock,
    product?.product?.availability?.num_available,
    product?.product?.availability?.num_in_stock,
    product?.product?.availability?.stock
  );
  const stockCount = Number(rawStockCount ?? 0);
  const hasExplicitStockCount = rawStockCount !== null && rawStockCount !== undefined && rawStockCount !== "";
  const explicitlyUnavailable =
    product?.is_available === false ||
    product?.availability?.is_available === false ||
    product?.availability?.is_available_to_buy === false ||
    product?.product?.is_available === false ||
    product?.product?.availability?.is_available === false ||
    product?.product?.availability?.is_available_to_buy === false;
  const explicitlyInStock = product?.in_stock === true || product?.product?.in_stock === true;

  if (!explicitlyUnavailable && ((hasExplicitStockCount && stockCount > 0) || (!hasExplicitStockCount && explicitlyInStock))) {
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

function firstValue(...values) {
  return values.find((value) => value !== null && value !== undefined && value !== "");
}
