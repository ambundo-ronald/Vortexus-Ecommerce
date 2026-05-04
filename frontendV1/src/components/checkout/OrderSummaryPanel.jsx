import { Link } from "react-router-dom";

import MaterialIcon from "../ui/MaterialIcon.jsx";
import { formatCurrency } from "../../utils/currency";

export default function OrderSummaryPanel({ basket, shipping, action, actionTo, loading = false }) {
  const totals = shipping?.totals || basket?.totals || {};
  const lines = basket?.lines || [];
  const currency = totals.currency || basket?.currency || "USD";
  const subtotal = totals.subtotal ?? basket?.totals?.subtotal ?? 0;
  const shippingTotal = totals.shipping ?? 0;
  const tax = totals.tax ?? 0;
  const orderTotal = totals.order_total ?? subtotal;

  return (
    <aside className="checkout-summary surface-panel">
      <div className="checkout-summary__head">
        <h2>Summary</h2>
        <span>{basket?.item_count || 0} items</span>
      </div>

      <div className="checkout-mini-lines">
        {lines.slice(0, 3).map((line) => (
          <div className="checkout-mini-line" key={line.id}>
            <span>{line.quantity}x</span>
            <strong>{line.product?.title || "Product"}</strong>
            <em>{formatCurrency(line.line_total, line.currency || currency)}</em>
          </div>
        ))}
        {lines.length > 3 ? <p>+{lines.length - 3} more item{lines.length - 3 === 1 ? "" : "s"}</p> : null}
      </div>

      <div className="checkout-totals">
        <div>
          <span>Subtotal</span>
          <strong>{formatCurrency(subtotal, currency)}</strong>
        </div>
        {shipping ? (
          <>
            <div>
              <span>Delivery</span>
              <strong>{formatCurrency(shippingTotal, currency)}</strong>
            </div>
            <div>
              <span>Tax</span>
              <strong>{formatCurrency(tax, currency)}</strong>
            </div>
          </>
        ) : null}
        <div className="checkout-total-row">
          <span>Total</span>
          <strong>{formatCurrency(orderTotal, currency)}</strong>
        </div>
      </div>

      {action && actionTo ? (
        <Link className="primary-button" to={actionTo}>
          <MaterialIcon name="arrow_forward" size={19} />
          {action}
        </Link>
      ) : null}
      {loading ? <p className="checkout-note">Updating summary...</p> : null}
    </aside>
  );
}
