export function formatCurrency(value, currency = "USD") {
  if (value === null || value === undefined || value === "") return "Quote on request";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 2
  }).format(Number(value));
}
