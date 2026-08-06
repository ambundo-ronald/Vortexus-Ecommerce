export function checkoutTaxTotal(totals = {}) {
  return numberOrZero(
    totals.tax ??
      totals.total_tax ??
      totals.taxes?.total_tax ??
      totals.tax_breakdown?.total_tax
  );
}

export function normalizeCheckoutTotals({ basket, shipping, preview } = {}) {
  const previewTotals = preview?.totals || {};
  const shippingTotals = shipping?.totals || {};
  const basketTotals = basket?.totals || {};
  const totals = Object.keys(previewTotals).length
    ? previewTotals
    : Object.keys(shippingTotals).length
      ? shippingTotals
      : basketTotals;

  const currency = totals.currency || shippingTotals.currency || basketTotals.currency || basket?.currency || "KES";
  const subtotal = numberOrZero(totals.subtotal ?? basketTotals.subtotal);
  const shippingTotal = numberOrZero(totals.shipping ?? shippingTotals.shipping);
  const tax = checkoutTaxTotal({
    ...shipping?.taxes,
    ...preview?.taxes,
    ...totals,
    taxes: totals.taxes || preview?.taxes || shipping?.taxes
  });
  const orderTotal = numberOrZero(
    totals.order_total ??
      totals.total ??
      totals.total_incl_tax ??
      subtotal + shippingTotal + tax
  );

  return {
    ...totals,
    currency,
    subtotal,
    shipping: shippingTotal,
    tax,
    order_total: orderTotal
  };
}

export function taxStatusLabel(status) {
  const normalized = String(status || "").trim().toLowerCase();
  if (normalized === "tax_exempt") return "Tax exempt";
  if (normalized === "zero_rated") return "Zero-rated";
  if (normalized === "taxable") return "Taxable";
  return "";
}

export function basketTaxStatuses(basket = {}) {
  const statuses = new Set();
  const breakdown = basket.tax_breakdown?.line_breakdown || basket.taxes?.line_breakdown || [];

  for (const item of breakdown) {
    const status = item.tax_status || item.taxStatus;
    if (status) statuses.add(status);
  }

  for (const line of basket.lines || []) {
    const status = line.tax_status || line.taxStatus || line.product?.tax_status || line.product?.taxStatus;
    if (status) statuses.add(status);
  }

  return [...statuses].map(taxStatusLabel).filter(Boolean);
}

function numberOrZero(value) {
  const number = Number(value);
  return Number.isFinite(number) ? number : 0;
}
