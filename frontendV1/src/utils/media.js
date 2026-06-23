import { buildMediaUrl } from "./urlConfig";

const API_ORIGIN = import.meta.env.VITE_API_BASE_URL || "";

export function mediaUrl(path) {
  return buildMediaUrl(path, API_ORIGIN);
}
