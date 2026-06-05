const EMAIL_EVENT_META = {
  account_registered: {
    icon: "person_add",
    label: "Account welcome",
    tone: "success"
  },
  email_verification: {
    icon: "verified_user",
    label: "Email verification",
    tone: "info"
  },
  account_reactivation_request: {
    icon: "support_agent",
    label: "Account reactivation",
    tone: "warning"
  },
  password_reset: {
    icon: "lock_reset",
    label: "Password reset",
    tone: "warning"
  },
  email_two_factor: {
    icon: "shield_lock",
    label: "Sign-in code",
    tone: "security"
  },
  password_changed: {
    icon: "admin_panel_settings",
    label: "Password changed",
    tone: "security"
  },
  quote_request_customer: {
    icon: "request_quote",
    label: "Quote request",
    tone: "info"
  },
  quote_request_internal: {
    icon: "request_quote",
    label: "Quote request",
    tone: "info"
  },
  order_confirmation: {
    icon: "receipt_long",
    label: "Order confirmation",
    tone: "success"
  },
  shipping_update: {
    icon: "local_shipping",
    label: "Delivery update",
    tone: "info"
  }
};

export function readableEmailEvent(value = "") {
  return String(value || "Message").replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function emailEventMeta(eventType = "") {
  const key = String(eventType || "").trim();
  return EMAIL_EVENT_META[key] || {
    icon: key.includes("shipping") || key.includes("delivery") ? "local_shipping" : "mail",
    label: readableEmailEvent(key),
    tone: "info"
  };
}

export function emailStatusLabel(status = "") {
  const value = String(status || "").trim().toLowerCase();
  if (!value) return "Recorded";
  if (value === "sent") return "Sent";
  if (value === "queued" || value === "pending") return "Queued";
  if (value === "failed" || value === "failure") return "Needs attention";
  if (value === "skipped") return "Skipped";
  return readableEmailEvent(value);
}
