import { Link } from "react-router-dom";

import MaterialIcon from "../ui/MaterialIcon.jsx";
import { formatCurrency } from "../../utils/currency";

export default function CartSummary({ basket }) {
  const totals = basket?.totals || {};
  return (
    <aside className="cart-summary surface-panel">
      <h2>Order summary</h2>
      <div className="summary-row">
        <span>Items</span>
        <strong>{basket?.item_count || 0}</strong>
      </div>
      <div className="summary-row">
        <span>Subtotal</span>
        <strong>{formatCurrency(totals.subtotal, totals.currency)}</strong>
      </div>
      <Link className="primary-button" to="/checkout/shipping">
        <MaterialIcon name="local_shipping" size={19} />
        Continue to shipping
      </Link>
    </aside>
  );
}
