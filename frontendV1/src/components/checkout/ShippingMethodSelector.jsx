import MaterialIcon from "../ui/MaterialIcon.jsx";
import { formatCurrency } from "../../utils/currency";

export default function ShippingMethodSelector({
  methods = [],
  selectedCode = "",
  saving = false,
  estimated = false,
  title = "Delivery method",
  note = "",
  onSelect
}) {
  if (!methods.length) {
    return (
      <section className="checkout-card">
        <div className="checkout-card__title">
          <span><MaterialIcon name="local_shipping" size={20} /></span>
          <div>
            <h2>{title}</h2>
            {note ? <p>{note}</p> : null}
          </div>
        </div>
        {estimated ? <p className="checkout-note">Pin your delivery location to calculate exact delivery choices.</p> : null}
      </section>
    );
  }

  return (
    <section className="checkout-card">
      <div className="checkout-card__title">
          <span><MaterialIcon name="local_shipping" size={20} /></span>
          <div>
          <h2>{title}</h2>
          {note ? <p>{note}</p> : null}
        </div>
      </div>

      <div className="choice-list">
        {methods.map((method) => {
          const active = selectedCode === method.code || method.selected;
          const disabled = saving || estimated || method.needs_location;
          return (
            <button
              className={`choice-card ${active ? "active" : ""}`}
              type="button"
              key={method.code}
              disabled={disabled}
              onClick={() => onSelect?.(method.code)}
            >
              <span className="choice-card__icon">
                <MaterialIcon name={method.is_pickup ? "storefront" : "local_shipping"} size={22} />
              </span>
              <span className="choice-card__copy">
                <strong>
                  {method.name}
                  {method.estimated || estimated ? <em className={method.needs_location ? "muted" : ""}>{method.estimate_label || "Estimate"}</em> : null}
                </strong>
                <small>{deliveryDescription(method)}</small>
                {method.estimate_note ? <small>{method.estimate_note}</small> : null}
              </span>
              <span className="choice-card__price">{deliveryPrice(method)}</span>
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

function deliveryDescription(method) {
  if (method?.method_type === "distance_delivery") {
    return method.description || deliveryEta(method);
  }
  return method.description || deliveryEta(method);
}

function deliveryPrice(method) {
  if (method?.needs_location && !Number(method?.charge)) return "After pinning";
  const price = formatCurrency(method?.charge, method?.currency);
  return method?.needs_location ? `From ${price}` : price;
}
