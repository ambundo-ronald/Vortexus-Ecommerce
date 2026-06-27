import { normalizeApiError } from "./errorHandler";

const CHECKOUT_ERROR_COPY = {
  cart_empty: {
    tone: "warning",
    title: "Your cart is empty",
    message: "Add products to your cart before checkout.",
    actionLabel: "Shop products",
    actionPath: "/shop"
  },
  cart_item_unavailable: {
    tone: "warning",
    title: "An item needs attention",
    message: "One or more cart items changed. Review your cart before continuing.",
    actionLabel: "Review cart",
    actionPath: "/checkout/cart"
  },
  shipping_missing: {
    tone: "warning",
    title: "Delivery details needed",
    message: "Add a delivery address and choose a delivery method before payment.",
    actionLabel: "Go to delivery",
    actionPath: "/checkout/shipping"
  },
  shipping_address_invalid: {
    tone: "warning",
    title: "Check the delivery address",
    message: "Some delivery details need correction before checkout can continue.",
    actionLabel: "Edit delivery",
    actionPath: "/checkout/shipping"
  },
  shipping_method_missing: {
    tone: "warning",
    title: "Choose a delivery method",
    message: "Select how this order should be delivered before payment.",
    actionLabel: "Go to delivery",
    actionPath: "/checkout/shipping"
  },
  payment_method_unavailable: {
    tone: "warning",
    title: "Payment method unavailable",
    message: "Choose another payment method or try again shortly.",
    actionLabel: "Change payment",
    actionPath: "/checkout/payment"
  },
  payment_requires_action: {
    tone: "info",
    title: "Complete payment",
    message: "Finish the payment step before reviewing this order.",
    actionLabel: "Go to payment",
    actionPath: "/checkout/payment"
  },
  payment_pending: {
    tone: "info",
    title: "Payment still pending",
    message: "Confirm the payment on your phone or payment provider, then check again.",
    actionLabel: "Check status",
    actionPath: ""
  },
  payment_failed: {
    tone: "warning",
    title: "Payment was not completed",
    message: "No confirmed payment was received. Retry or choose another payment method.",
    actionLabel: "Change payment",
    actionPath: "/checkout/payment"
  },
  payment_timeout: {
    tone: "warning",
    title: "Payment is taking longer than expected",
    message: "Confirm the prompt on your phone or try another payment method.",
    actionLabel: "Check status",
    actionPath: ""
  },
  payment_cancelled: {
    tone: "warning",
    title: "Payment was cancelled",
    message: "No money was collected. You can retry or choose another payment method.",
    actionLabel: "Change payment",
    actionPath: "/checkout/payment"
  },
  order_preview_failed: {
    tone: "danger",
    title: "Could not prepare checkout",
    message: "Refresh the checkout summary and try again.",
    actionLabel: "Retry",
    actionPath: ""
  },
  order_place_failed: {
    tone: "danger",
    title: "Order could not be placed",
    message: "Your order was not created. Check the details and try again.",
    actionLabel: "Try again",
    actionPath: ""
  },
  confirmation_missing: {
    tone: "warning",
    title: "Order confirmation unavailable",
    message: "We could not find a recent order confirmation.",
    actionLabel: "View orders",
    actionPath: "/account/orders"
  },
  auth_required: {
    tone: "warning",
    title: "Sign in required",
    message: "Sign in to continue checkout.",
    actionLabel: "Sign in",
    actionPath: "/login"
  },
  network_error: {
    tone: "danger",
    title: "Connection problem",
    message: "Check your internet connection and try again.",
    actionLabel: "Retry",
    actionPath: ""
  },
  server_error: {
    tone: "danger",
    title: "Checkout is temporarily unavailable",
    message: "Something went wrong on our side. Try again shortly.",
    actionLabel: "Retry",
    actionPath: ""
  },
  unknown_error: {
    tone: "danger",
    title: "Checkout problem",
    message: "Something went wrong. Try again.",
    actionLabel: "Try again",
    actionPath: ""
  }
};

const FIELD_CODE_HINTS = {
  address: "shipping_address_invalid",
  address_id: "shipping_address_invalid",
  line1: "shipping_address_invalid",
  phone_number: "shipping_address_invalid",
  selected_method: "shipping_method_missing",
  method_code: "shipping_method_missing",
  payment_method: "payment_method_unavailable",
  method: "payment_method_unavailable",
  basket: "cart_item_unavailable",
  lines: "cart_item_unavailable"
};

export function checkoutErrorView(error, context = "") {
  const normalized = normalizeApiError(error, CHECKOUT_ERROR_COPY.unknown_error.message);
  const code = checkoutErrorCode(normalized, context);
  const copy = CHECKOUT_ERROR_COPY[code] || CHECKOUT_ERROR_COPY.unknown_error;

  return {
    ...copy,
    code,
    status: normalized.status || null,
    message: customerMessage(normalized, copy),
    errors: normalized.errors || null,
    originalMessage: normalized.message || ""
  };
}

export function checkoutErrorCode(normalized = {}, context = "") {
  const explicitCode = String(normalized.code || "").toLowerCase();
  const status = Number(normalized.status || 0);
  const message = String(normalized.message || "").toLowerCase();
  const fieldCode = fieldErrorCode(normalized.errors);

  if (explicitCode && !["request_error", "unknown_error", "validation_error"].includes(explicitCode) && CHECKOUT_ERROR_COPY[explicitCode]) return explicitCode;
  if (context === "payment_status" && /pending|confirm|prompt|stk/.test(message)) return "payment_pending";
  if (context === "payment" && /cancel/.test(message)) return "payment_cancelled";
  if (context === "payment" && /failed|not completed|declined|rejected/.test(message)) return "payment_failed";
  if (context === "payment" && /pending|confirm the prompt|taking longer/.test(message)) return "payment_timeout";
  if (context === "payment" && /not available|unavailable|not configured|choose another payment/.test(message)) return "payment_method_unavailable";
  if (context === "shipping" && fieldCode) return fieldCode;
  if (context === "preview" && /shipping|delivery|address/.test(message)) return "shipping_missing";
  if (context === "place_order" && /stock|unavailable|basket|cart/.test(message)) return "cart_item_unavailable";
  if (fieldCode) return fieldCode;
  if (status === 401 || status === 403) return "auth_required";
  if (status === 0 || /network|failed to fetch|connection/.test(message)) return "network_error";
  if (status >= 500) return "server_error";
  if (context === "preview") return "order_preview_failed";
  if (context === "place_order") return "order_place_failed";
  if (context === "confirmation") return "confirmation_missing";
  return "unknown_error";
}

export function checkoutToastPayload(error, context = "") {
  const view = checkoutErrorView(error, context);
  return {
    tone: view.tone,
    title: view.title,
    message: view.message,
    icon: view.tone === "warning" ? "info" : "error"
  };
}

function fieldErrorCode(errors) {
  if (!errors || typeof errors !== "object") return "";
  for (const key of Object.keys(errors)) {
    if (FIELD_CODE_HINTS[key]) return FIELD_CODE_HINTS[key];
    const nested = fieldErrorCode(errors[key]);
    if (nested) return nested;
  }
  return "";
}

function customerMessage(normalized, copy) {
  const message = normalized.message || "";
  if (!message) return copy.message;
  if (normalized.status >= 500) return copy.message;
  if (/request failed|network error/i.test(message)) return copy.message;
  return message;
}
