import { useNavigate } from "react-router-dom";

import MaterialIcon from "../ui/MaterialIcon.jsx";

const STEPS = [
  { key: "cart", label: "Cart", icon: "shopping_cart", path: "/checkout/cart" },
  { key: "checkout", label: "Checkout", icon: "local_shipping", path: "/checkout" },
  { key: "done", label: "Done", icon: "check_circle", path: "/checkout/confirmation" }
];

export default function CheckoutStepper({ current = "cart", basket, orderNumber = "" }) {
  const navigate = useNavigate();
  const normalizedCurrent = ["shipping", "payment", "review"].includes(current) ? "checkout" : current;
  const activeIndex = Math.max(0, STEPS.findIndex((step) => step.key === normalizedCurrent));
  const lastOrderNumber = orderNumber || readLastOrderNumber();

  function routeForStep(step, index) {
    const hasKnownEmptyBasket = basket?.is_empty === true;

    if (step.key === "cart") return "/checkout/cart";
    if (hasKnownEmptyBasket) return "/checkout/cart";
    if (step.key === "checkout") return "/checkout";
    if (step.key === "done") {
      if (lastOrderNumber) return `/checkout/confirmation?order_number=${encodeURIComponent(lastOrderNumber)}`;
      return "/checkout";
    }
    return index <= activeIndex ? step.path : STEPS[Math.min(activeIndex + 1, STEPS.length - 1)].path;
  }

  return (
    <nav className="checkout-stepper" aria-label="Checkout progress">
      {STEPS.map((step, index) => (
        <button
          className={`checkout-step ${index <= activeIndex ? "active" : ""}`}
          type="button"
          aria-current={step.key === normalizedCurrent ? "step" : undefined}
          onClick={() => navigate(routeForStep(step, index))}
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

function readLastOrderNumber() {
  try {
    const payload = JSON.parse(sessionStorage.getItem("vortexus:lastOrder") || "null");
    return payload?.order?.number || payload?.order?.order_number || "";
  } catch {
    return "";
  }
}
