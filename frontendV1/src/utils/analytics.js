import { analyticsApi } from "../api/analytics.api";

const recentEvents = new Map();
const DEDUPE_WINDOW_MS = 1200;
const ANONYMOUS_ID_KEY = "reesolmart:anonymousAnalyticsId";
const LAST_SEARCH_KEY = "reesolmart:lastSearchContext";

function randomId(prefix) {
  const cryptoObject = typeof crypto !== "undefined" ? crypto : null;
  if (cryptoObject?.randomUUID) return `${prefix}_${cryptoObject.randomUUID()}`;
  return `${prefix}_${Date.now()}_${Math.random().toString(36).slice(2, 12)}`;
}

export function getAnonymousAnalyticsId() {
  if (typeof localStorage === "undefined") return "";
  let value = localStorage.getItem(ANONYMOUS_ID_KEY);
  if (!value) {
    value = randomId("anon");
    localStorage.setItem(ANONYMOUS_ID_KEY, value);
  }
  return value;
}

export function rememberSearchContext(metadata = {}) {
  if (typeof sessionStorage === "undefined") return null;
  const context = {
    search_context_id: metadata.search_context_id || randomId("search"),
    search: metadata.search || metadata.query || "",
    source: metadata.source || "text",
    category: metadata.category || "",
    brand: metadata.brand || "",
    result_count: metadata.result_count,
    created_at: new Date().toISOString()
  };
  sessionStorage.setItem(LAST_SEARCH_KEY, JSON.stringify(context));
  return context;
}

export function getLastSearchContext() {
  if (typeof sessionStorage === "undefined") return null;
  try {
    const context = JSON.parse(sessionStorage.getItem(LAST_SEARCH_KEY) || "null");
    if (!context?.search_context_id) return null;
    const ageMs = Date.now() - Date.parse(context.created_at || 0);
    return ageMs < 24 * 60 * 60 * 1000 ? context : null;
  } catch {
    return null;
  }
}

export function searchAttributionMetadata(extra = {}) {
  const context = getLastSearchContext();
  return context ? { ...context, ...extra } : extra;
}

function cleanMetadata(metadata = {}) {
  return Object.fromEntries(
    Object.entries(metadata)
      .filter(([, value]) => value !== undefined && value !== "")
      .map(([key, value]) => [key, typeof value === "string" ? value.slice(0, 255) : value])
  );
}

export function trackStorefrontEvent(event, metadata = {}) {
  const anonymous_id = getAnonymousAnalyticsId();
  const payload = {
    event_type: event,
    metadata: cleanMetadata({ anonymous_id, ...metadata })
  };
  const signature = JSON.stringify(payload);
  const now = Date.now();
  const lastSent = recentEvents.get(signature) || 0;
  if (now - lastSent < DEDUPE_WINDOW_MS) return;
  recentEvents.set(signature, now);

  void analyticsApi.track(payload).catch(() => {
    // Analytics must never interrupt the customer flow.
  });
}
