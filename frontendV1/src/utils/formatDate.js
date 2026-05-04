export function formatDate(value, options = {}) {
  if (!value) return "";
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: options.time ? "short" : undefined
  }).format(new Date(value));
}
