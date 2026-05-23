import { analyticsApi } from "../api/analytics.api";

const recentEvents = new Map();
const DEDUPE_WINDOW_MS = 1200;

function cleanMetadata(metadata = {}) {
  return Object.fromEntries(
    Object.entries(metadata)
      .filter(([, value]) => value !== undefined && value !== "")
      .map(([key, value]) => [key, typeof value === "string" ? value.slice(0, 255) : value])
  );
}

export function trackStorefrontEvent(event, metadata = {}) {
  const payload = {
    event_type: event,
    metadata: cleanMetadata(metadata)
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
