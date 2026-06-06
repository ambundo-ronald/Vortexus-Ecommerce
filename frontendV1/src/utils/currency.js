const SUPPORTED_CURRENCIES = new Set(["KES", "USD", "UGX", "TZS", "RWF", "ETB"]);

export function formatCurrency(value, currency = "KES") {
  if (value === null || value === undefined || value === "") return "Quote on request";
  const resolvedCurrency = SUPPORTED_CURRENCIES.has(String(currency || "").toUpperCase())
    ? String(currency).toUpperCase()
    : "KES";
  return new Intl.NumberFormat(resolvedCurrency === "KES" ? "en-KE" : "en-US", {
    style: "currency",
    currency: resolvedCurrency,
    maximumFractionDigits: 2
  }).format(Number(value));
}

export function storefrontCurrency() {
  if (typeof window === "undefined") return "KES";

  let storedCurrency = "";
  try {
    storedCurrency = (window.localStorage?.getItem("vortexus_currency") || "").toUpperCase();
  } catch {
    storedCurrency = "";
  }
  if (SUPPORTED_CURRENCIES.has(storedCurrency)) return storedCurrency;

  const languages = navigator.languages?.length ? navigator.languages : [navigator.language].filter(Boolean);
  const hasKenyaLocale = languages.some((language) => /(^|-)(ke)$/i.test(language));
  const timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;

  return "KES";
}
