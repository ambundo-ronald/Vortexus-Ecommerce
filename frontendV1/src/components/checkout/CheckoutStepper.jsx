import MaterialIcon from "../ui/MaterialIcon.jsx";

const STEPS = [
  { key: "cart", label: "Cart", icon: "shopping_cart" },
  { key: "shipping", label: "Shipping", icon: "local_shipping" },
  { key: "payment", label: "Pay", icon: "payments" },
  { key: "done", label: "Done", icon: "check_circle" }
];

export default function CheckoutStepper({ current = "cart" }) {
  const activeIndex = Math.max(0, STEPS.findIndex((step) => step.key === current));

  return (
    <nav className="checkout-stepper" aria-label="Checkout progress">
      {STEPS.map((step, index) => (
        <div
          className={`checkout-step ${index <= activeIndex ? "active" : ""}`}
          key={step.key}
        >
          <span>
            <MaterialIcon name={step.icon} size={18} />
          </span>
          <strong>{step.label}</strong>
        </div>
      ))}
    </nav>
  );
}
