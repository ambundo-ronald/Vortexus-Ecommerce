function firstValidationMessage(errors) {
  if (!errors) return "";
  if (typeof errors === "string") return errors;
  if (Array.isArray(errors)) {
    return errors.map(firstValidationMessage).find(Boolean) || "";
  }
  if (typeof errors === "object") {
    for (const [field, value] of Object.entries(errors)) {
      const message = firstValidationMessage(value);
      if (!message) continue;
      if (field === "non_field_errors" || field === "detail") return message;
      return `${field.replaceAll("_", " ")}: ${message}`;
    }
  }
  return "";
}

export function normalizeApiError(error, fallback = "Something went wrong.") {
  if (error?.normalized) return error.normalized;
  const payload = error?.response?.data;
  return {
    message:
      firstValidationMessage(payload?.error?.errors) ||
      firstValidationMessage(payload?.errors) ||
      payload?.error?.detail ||
      payload?.detail ||
      error?.message ||
      fallback,
    status: payload?.error?.status || error?.response?.status || null,
    code: payload?.error?.code || "unknown_error",
    errors: payload?.error?.errors || null
  };
}
