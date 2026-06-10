export function normalizeOrigin(value = "") {
  return String(value).trim().replace(/\/+$/, "");
}

export function normalizePath(value = "", fallback = "") {
  const path = String(value || fallback).trim();
  if (!path) return "";
  return `/${path.replace(/^\/+|\/+$/g, "")}`;
}

export function buildApiRoot(origin, prefix = "/api/v1") {
  const normalizedOrigin = normalizeOrigin(origin);
  const normalizedPrefix = normalizePath(prefix, "/api/v1");

  if (!normalizedOrigin) return normalizedPrefix;
  if (normalizedOrigin.endsWith(normalizedPrefix)) return normalizedOrigin;
  return `${normalizedOrigin}${normalizedPrefix}`;
}

export function buildMediaUrl(path, apiOrigin = "") {
  if (!path) return "";
  if (/^(?:https?:|blob:|data:)/i.test(path)) return path;

  const normalizedOrigin = normalizeOrigin(apiOrigin);
  if (!normalizedOrigin || normalizedOrigin.startsWith("/")) return path;

  try {
    return new URL(path, `${normalizedOrigin}/`).toString();
  } catch {
    return `${normalizedOrigin}${path.startsWith("/") ? path : `/${path}`}`;
  }
}
