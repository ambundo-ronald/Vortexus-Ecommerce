import { useNavigate, useSearchParams } from "react-router-dom";

import MaterialIcon from "../ui/MaterialIcon.jsx";
import { useUiStore } from "../../store/ui.store";
import { readPendingCheckout } from "../../utils/payment";

const STEPS = [
  { key: "cart", label: "Cart", icon: "shopping_cart", path: "/checkout/cart" },
  { key: "shipping", label: "Shipping", icon: "local_shipping", path: "/checkout/shipping" },
  { key: "payment", label: "Pay", icon: "payments", path: "/checkout/payment" },
  { key: "review", label: "Review", icon: "fact_check", path: "/checkout/review" },
  { key: "done", label: "Done", icon: "check_circle", path: "/checkout/confirmation" }
];

export default function CheckoutStepper({ current = "cart", basket, shipping, pendingCheckout, orderNumber = "" }) {
  const navigate = useNavigate();
  const notify = useUiStore((state) => state.notify);
  const [searchParams] = useSearchParams();
  const activeIndex = Math.max(0, STEPS.findIndex((step) => step.key === current));
  const pending = pendingCheckout || readPendingCheckout(searchParams);
  const lastOrderNumber = orderNumber || readLastOrderNumber();

  function routeForStep(step, index) {
    const hasKnownEmptyBasket = basket?.is_empty === true;
    const shippingReady = Boolean(shipping?.ready_for_checkout);
    const hasPendingPayment = Boolean(pending?.payment_reference);

    if (step.key === "cart") return "/checkout/cart";
    if (hasKnownEmptyBasket) return "/checkout/cart";
    if (step.key === "shipping") return "/checkout/shipping";
    if (step.key === "payment") return shippingReady || activeIndex >= 2 ? "/checkout/payment" : "/checkout/shipping";
    if (step.key === "review") {
      if (hasPendingPayment) return "/checkout/review";
      if (!shippingReady && activeIndex < 2) return "/checkout/shipping";
      return "/checkout/payment";
    }
    if (step.key === "done") {
      if (lastOrderNumber) return `/checkout/confirmation?order_number=${encodeURIComponent(lastOrderNumber)}`;
      if (hasPendingPayment) return "/checkout/review";
      if (!shippingReady && activeIndex < 2) return "/checkout/shipping";
      return activeIndex >= 3 ? "/checkout/review" : "/checkout/payment";
    }
    return index <= activeIndex ? step.path : STEPS[Math.min(activeIndex + 1, STEPS.length - 1)].path;
  }

  function handleStepClick(step, index) {
    const target = routeForStep(step, index);
    const message = blockedStepMessage(step, target);
    if (message) {
      notify({
        tone: "info",
        title: message.title,
        message: message.message,
        icon: "info"
      });
    }
    navigate(target);
  }

  return (
    <nav className="checkout-stepper" aria-label="Checkout progress">
      {STEPS.map((step, index) => (
        <button
          className={`checkout-step ${index <= activeIndex ? "active" : ""}`}
          type="button"
          aria-current={step.key === current ? "step" : undefined}
          onClick={() => handleStepClick(step, index)}
          key={step.key}
        >
          <span>
            <MaterialIcon name={step.icon} size={18} />
          </span>
          <strong>{step.label}</strong>
        </button>
      ))}
    </nav>
  );
}

function blockedStepMessage(step, target) {
  if (step.path === target || (step.key === "done" && target.startsWith(step.path))) return null;
  if (target === "/checkout/cart") {
    return {
      title: "Cart needs products",
      message: "Add products to your cart before continuing checkout."
    };
  }
  if (target === "/checkout/shipping") {
    return {
      title: "Delivery comes first",
      message: "Add delivery details before moving to payment or review."
    };
  }
  if (target === "/checkout/payment") {
    return {
      title: "Complete payment first",
      message: "Choose a payment method before reviewing or finishing the order."
    };
  }
  if (target === "/checkout/review") {
    return {
      title: "Review your order",
      message: "Confirm the order details before opening the final confirmation."
    };
  }
  return null;
}

function readLastOrderNumber() {
  try {
    const payload = JSON.parse(sessionStorage.getItem("vortexus:lastOrder") || "null");
    return payload?.order?.number || payload?.order?.order_number || "";
  } catch {
    return "";
  }
}
