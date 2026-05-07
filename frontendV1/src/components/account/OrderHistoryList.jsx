import { Link } from "react-router-dom";

import MaterialIcon from "../ui/MaterialIcon.jsx";
import { formatCurrency } from "../../utils/currency";
import { formatDate } from "../../utils/formatDate";

export default function OrderHistoryList({ orders = [] }) {
  if (!orders.length) {
    return (
      <div className="empty-state">
        <strong>No orders yet</strong>
        <p>Your completed orders will appear here.</p>
        <Link className="primary-button empty-state__action" to="/catalog">
          <MaterialIcon name="storefront" size={18} />
          Shop now
        </Link>
      </div>
    );
  }

  return (
    <div className="order-list">
      {orders.map((order) => (
        <Link className="order-list-card" to={`/account/orders/${order.number}`} key={order.id || order.number}>
          <span className="order-list-card__icon"><MaterialIcon name="receipt_long" size={22} /></span>
          <span className="order-list-card__main">
            <strong>Order #{order.number}</strong>
            <small>{formatDate(order.date_placed)} · {order.item_count || 0} items</small>
          </span>
          <span className="order-list-card__side">
            <em>{order.status || "Pending"}</em>
            <strong>{formatCurrency(order.total_incl_tax, order.currency)}</strong>
          </span>
        </Link>
      ))}
    </div>
  );
}
