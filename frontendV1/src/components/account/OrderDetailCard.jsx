import { Link } from "react-router-dom";

import MaterialIcon from "../ui/MaterialIcon.jsx";
import { formatCurrency } from "../../utils/currency";
import { formatDate } from "../../utils/formatDate";
import { productPlaceholderImage } from "../../utils/productImages";

export default function OrderDetailCard({ order, saving = false, onReorder }) {
  if (!order) return null;
  const address = order.shipping_address;
  const totals = order.totals || {};

  return (
    <article className="order-detail">
      <section className="surface-panel order-detail__hero">
        <div>
          <p className="eyebrow">Order</p>
          <h1>#{order.number}</h1>
          <p>{formatDate(order.date_placed)} · {order.status}</p>
        </div>
        <button className="secondary-button" type="button" disabled={saving} onClick={() => onReorder?.(order.number)}>
          <MaterialIcon name="replay" size={18} />
          Reorder
        </button>
      </section>

      <section className="account-detail-grid">
        <div className="account-info-card">
          <MaterialIcon name="payments" size={22} />
          <span>Total</span>
          <strong>{formatCurrency(totals.total_incl_tax, order.currency)}</strong>
        </div>
        <div className="account-info-card">
          <MaterialIcon name="local_shipping" size={22} />
          <span>Delivery</span>
          <strong>{order.shipping_method || "Saved"}</strong>
        </div>
      </section>

      {address ? (
        <section className="checkout-card">
          <div className="checkout-card__title">
            <span><MaterialIcon name="location_on" size={20} /></span>
            <div>
              <h2>Delivery address</h2>
              <p>{[address.line1, address.line2, address.line4, address.country_code].filter(Boolean).join(", ")}</p>
            </div>
          </div>
        </section>
      ) : null}

      <section className="checkout-card">
        <div className="checkout-card__title">
          <span><MaterialIcon name="inventory_2" size={20} /></span>
          <div>
            <h2>Items</h2>
            <p>{order.lines?.length || 0} line{order.lines?.length === 1 ? "" : "s"}</p>
          </div>
        </div>
        <div className="order-line-list">
          {(order.lines || []).map((line, index) => (
            <Link className="order-line-card" to={line.product_id ? `/products/${line.product_id}` : "/catalog"} key={line.id || index}>
              <img src={productPlaceholderImage(index)} alt={line.title || "Product"} />
              <span>
                <strong>{line.title || line.product_title || "Product"}</strong>
                <small>Qty {line.quantity}</small>
              </span>
              <em>{formatCurrency(line.line_price_incl_tax || line.total_incl_tax || line.price_incl_tax, order.currency)}</em>
            </Link>
          ))}
        </div>
      </section>
    </article>
  );
}
