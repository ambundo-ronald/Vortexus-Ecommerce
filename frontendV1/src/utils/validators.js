export function required(value) {
  return value !== null && value !== undefined && String(value).trim() !== "";
}

export function isEmail(value) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(value || "").trim());
}

export function isPositiveInteger(value) {
  return Number.isInteger(Number(value)) && Number(value) > 0;
}
