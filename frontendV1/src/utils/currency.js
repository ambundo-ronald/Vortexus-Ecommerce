export function formatCurrency(value, currency = "USD") {
  if (value === null || value === undefined || value === "") return "Quote on request";
  return new Intl.NumberFormat(currency === "KES" ? "en-KE" : "en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 2
  }).format(Number(value));
}

export function storefrontCurrency() {
  if (typeof window === "undefined") return "KES";

  let storedCurrency = "";
  try {
    storedCurrency = window.localStorage?.getItem("vortexus_currency") || "";
  } catch {
    storedCurrency = "";
  }
  if (storedCurrency === "KES" || storedCurrency === "USD") return storedCurrency;

  const languages = navigator.languages?.length ? navigator.languages : [navigator.language].filter(Boolean);
  const hasKenyaLocale = languages.some((language) => /(^|-)(ke)$/i.test(language));
  const timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;

  return hasKenyaLocale || timeZone === "Africa/Nairobi" ? "KES" : "USD";
}
