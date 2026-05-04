const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

export function mediaUrl(path) {
  if (!path) return "/images/placeholder.webp";
  if (/^https?:\/\//i.test(path)) return path;
  return `${API_BASE_URL}${path}`;
}
