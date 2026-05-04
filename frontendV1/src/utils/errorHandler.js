export function normalizeApiError(error, fallback = "Something went wrong.") {
  if (error?.normalized) return error.normalized;
  const payload = error?.response?.data;
  return {
    message: payload?.error?.detail || payload?.detail || error?.message || fallback,
    status: payload?.error?.status || error?.response?.status || null,
    code: payload?.error?.code || "unknown_error",
    errors: payload?.error?.errors || null
  };
}
