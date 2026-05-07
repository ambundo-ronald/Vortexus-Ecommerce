import MaterialIcon from "../ui/MaterialIcon.jsx";
import { formatCurrency } from "../../utils/currency";

export default function ShippingMethodSelector({ methods = [], selectedCode = "", saving = false, onSelect }) {
  if (!methods.length) {
    return (
      <section className="checkout-card">
        <div className="checkout-card__title">
          <span><MaterialIcon name="local_shipping" size={20} /></span>
          <div>
            <h2>Delivery method</h2>
            <p>Save your address to see available options.</p>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="checkout-card">
      <div className="checkout-card__title">
        <span><MaterialIcon name="local_shipping" size={20} /></span>
        <div>
          <h2>Delivery method</h2>
          <p>Choose the option that works for you.</p>
        </div>
      </div>

      <div className="choice-list">
        {methods.map((method) => {
          const active = selectedCode === method.code || method.selected;
          return (
            <button
              className={`choice-card ${active ? "active" : ""}`}
              type="button"
              key={method.code}
              disabled={saving}
              onClick={() => onSelect?.(method.code)}
            >
              <span className="choice-card__icon">
                <MaterialIcon name={method.is_pickup ? "storefront" : "local_shipping"} size={22} />
              </span>
              <span className="choice-card__copy">
                <strong>{method.name}</strong>
                <small>{method.description || deliveryEta(method)}</small>
              </span>
              <span className="choice-card__price">{formatCurrency(method.charge, method.currency)}</span>
            </button>
          );
        })}
      </div>
    </section>
  );
}

function deliveryEta(method) {
  const eta = method?.eta || {};
  if (!eta.min_days && !eta.max_days) return "Available for this order";
  if (eta.min_days === eta.max_days) return `${eta.min_days} day${eta.min_days === 1 ? "" : "s"}`;
  return `${eta.min_days || 1}-${eta.max_days} days`;
}
