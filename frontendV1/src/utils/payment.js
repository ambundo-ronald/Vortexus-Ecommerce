import { PAYMENT_METHOD_CODES, PREPAYMENT_METHODS } from "../constants/paymentMethods";

export const PAYMENT_COMPLETE_STATUSES = new Set(["authorized", "paid"]);
export const PAYMENT_FAILED_STATUSES = new Set(["cancelled", "failed"]);
export const PAYMENT_PENDING_STATUSES = new Set(["initialized", "pending"]);
export const PAYMENT_CONFIRMATION_TIMEOUT_MS = 5 * 60 * 1000;

const METHOD_COPY = {
  [PAYMENT_METHOD_CODES.PESAPAL]: {
    icon: "account_balance_wallet",
    shortName: "Pesapal",
    hint: "Continue to Pesapal's secure checkout.",
    pendingTitle: "Confirming your Pesapal payment",
    pendingMessage: "We are checking the payment result before your order can be placed."
  },
  [PAYMENT_METHOD_CODES.MPESA]: {
    icon: "phone_iphone",
    shortName: "M-Pesa",
    hint: "Approve the STK prompt sent to your phone.",
    pendingTitle: "Approve the M-Pesa prompt",
    pendingMessage: "Enter your M-Pesa PIN on your phone. Keep this page open while we confirm payment."
  },
  [PAYMENT_METHOD_CODES.AIRTEL_MONEY]: {
    icon: "phone_iphone",
    shortName: "Airtel Money",
    hint: "Approve the payment prompt sent to your phone.",
    pendingTitle: "Approve the Airtel Money prompt",
    pendingMessage: "Complete the Airtel Money request on your phone while we wait for confirmation."
  },
  [PAYMENT_METHOD_CODES.CREDIT_CARD]: {
    icon: "credit_card",
    shortName: "Credit card",
    hint: "Authorize a card payment securely."
  },
  [PAYMENT_METHOD_CODES.DEBIT_CARD]: {
    icon: "credit_card",
    shortName: "Debit card",
    hint: "Authorize a debit card payment securely."
  },
  [PAYMENT_METHOD_CODES.BANK_TRANSFER]: {
    icon: "account_balance",
    shortName: "Bank transfer",
    hint: "Place the order, then complete the transfer using its reference."
  },
  [PAYMENT_METHOD_CODES.CASH_ON_DELIVERY]: {
    icon: "payments",
    shortName: "Cash on delivery",
    hint: "Pay when the order is delivered."
  }
};

export function paymentMethodCopy(methodOrCode = "") {
  const code = typeof methodOrCode === "string" ? methodOrCode : methodOrCode?.code;
  return METHOD_COPY[code] || {
    icon: "payments",
    shortName: readablePaymentMethod(code),
    hint: "Available for this order."
  };
}

export function readablePaymentMethod(method = "") {
  return String(method || "")
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase()) || "Payment";
}

export function isPaymentComplete(paymentOrStatus) {
  const status = typeof paymentOrStatus === "string" ? paymentOrStatus : paymentOrStatus?.status;
  return PAYMENT_COMPLETE_STATUSES.has(status);
}

export function isPaymentFailed(paymentOrStatus) {
  const status = typeof paymentOrStatus === "string" ? paymentOrStatus : paymentOrStatus?.status;
  return PAYMENT_FAILED_STATUSES.has(status);
}

export function paymentRequiresPrepayment(method) {
  if (typeof method === "object" && method) return Boolean(method.requires_prepayment);
  return PREPAYMENT_METHODS.has(method);
}

export function paymentStatusView(payment) {
  const status = payment?.status || "initialized";
  const method = payment?.method || "";
  const copy = paymentMethodCopy(method);
  const providerMessage =
    payment?.provider_payload?.customer_message ||
    payment?.provider_payload?.response_description ||
    payment?.metadata?.pesapal_status ||
    payment?.metadata?.mpesa_result_desc ||
    "";

  if (status === "paid") {
    return {
      tone: "success",
      icon: "check_circle",
      label: "Paid",
      title: "Payment confirmed",
      message: providerMessage || "Your payment has been received and the order is ready to place."
    };
  }
  if (status === "authorized") {
    const offline = method === PAYMENT_METHOD_CODES.BANK_TRANSFER || method === PAYMENT_METHOD_CODES.CASH_ON_DELIVERY;
    return {
      tone: "success",
      icon: offline ? "verified" : "check_circle",
      label: offline ? "Order payment arranged" : "Authorized",
      title: offline ? `${copy.shortName} selected` : "Payment authorized",
      message: offline
        ? offlinePaymentInstructions(method, payment?.reference)
        : "The payment has been authorized and the order is ready to place."
    };
  }
  if (status === "failed") {
    return {
      tone: "danger",
      icon: "error",
      label: "Failed",
      title: "Payment was not completed",
      message: providerMessage || "The provider did not approve this payment. Try again or choose another method."
    };
  }
  if (status === "cancelled") {
    return {
      tone: "warning",
      icon: "cancel",
      label: "Cancelled",
      title: "Payment was cancelled",
      message: providerMessage || "No money was collected. You can retry or choose another payment method."
    };
  }
  return {
    tone: "info",
    icon: "hourglass_top",
    label: "Pending",
    title: copy.pendingTitle || "Payment is being confirmed",
    message: providerMessage || copy.pendingMessage || "Keep this page open while the provider confirms payment."
  };
}

export function offlinePaymentInstructions(method, reference = "") {
  if (method === PAYMENT_METHOD_CODES.CASH_ON_DELIVERY) {
    return "Pay when the order is delivered. No online payment is required now.";
  }
  if (method === PAYMENT_METHOD_CODES.BANK_TRANSFER) {
    return `Place the order to reserve the items. Use ${reference || "the order reference"} when making the bank transfer.`;
  }
  return "";
}

export function paymentReferenceFromSearch(searchParams) {
  if (!searchParams) return "";
  return (
    searchParams.get("OrderMerchantReference") ||
    searchParams.get("orderMerchantReference") ||
    searchParams.get("order_merchant_reference") ||
    ""
  ).trim();
}

export function storePendingCheckout(payload) {
  sessionStorage.setItem("vortexus:pendingCheckout", JSON.stringify(payload));
}

export function readPendingCheckout(searchParams) {
  let stored = null;
  try {
    stored = JSON.parse(sessionStorage.getItem("vortexus:pendingCheckout") || "null");
  } catch {
    stored = null;
  }

  if (stored?.payment_reference) return stored;

  const paymentReference = paymentReferenceFromSearch(searchParams);
  if (!paymentReference) return null;
  return {
    payment_reference: paymentReference,
    payment: {
      reference: paymentReference,
      method: PAYMENT_METHOD_CODES.PESAPAL,
      status: "pending"
    },
    method: {
      code: PAYMENT_METHOD_CODES.PESAPAL,
      name: "Pesapal",
      requires_prepayment: true
    },
    guest_email: ""
  };
}
