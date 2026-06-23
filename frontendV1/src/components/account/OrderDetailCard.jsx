import { Link } from "react-router-dom";

import EmailTouchpointCard from "./EmailTouchpointCard.jsx";
import MaterialIcon from "../ui/MaterialIcon.jsx";
import { formatCurrency } from "../../utils/currency";
import { formatDate } from "../../utils/formatDate";
import { productId, productInitials, productTitle } from "../../utils/productDisplay";
import { productImageUrl } from "../../utils/productImages";

export default function OrderDetailCard({ order, saving = false, onReorder }) {
  if (!order) return null;
  const address = order.shipping_address;
  const totals = order.totals || {};
  const accountOrder = Boolean(onReorder);
  const statusTimeline = order.status_timeline || order.status_snapshot?.timeline || [];
  const supplierGroups = Array.isArray(order.supplier_groups) ? order.supplier_groups : [];
  const trackingReferences = supplierGroups
    .map((group) => ({
      id: group.id,
      partner: group.partner?.name || "Supplier",
      status: group.status || "Processing",
      reference: group.tracking_reference || ""
    }))
    .filter((group) => group.reference);
  const latestReference = trackingReferences[0]?.reference || "";

  return (
    <article className="order-detail">
      <section className="surface-panel order-detail__hero">
        <div>
          <p className="eyebrow">Order</p>
          <h1>#{order.number}</h1>
          <p>{formatDate(order.date_placed)} · {order.status}</p>
        </div>
        {onReorder ? (
          <button className="secondary-button" type="button" disabled={saving} onClick={() => onReorder(order.number)}>
            <MaterialIcon name="replay" size={18} />
            Reorder
          </button>
        ) : null}
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

      <section className="order-email-flow">
        <EmailTouchpointCard
          actions={accountOrder ? [
            { to: "/account/messages", label: "Email history", icon: "inbox" },
            { to: "/account/preferences", label: "Email settings", icon: "tune" }
          ] : []}
          eyebrow="Order email updates"
          icon={latestReference ? "local_shipping" : "mark_email_read"}
          message={accountOrder
            ? "We email confirmations and delivery changes to your account address. You can review sent messages or adjust optional order emails from your account."
            : "This tracking page shows the latest order status. Delivery updates are also sent to the email address used at checkout."}
          meta={latestReference ? `Latest tracking reference: ${latestReference}` : "Tracking references appear here when dispatch is updated."}
          title={order.status ? `${order.status} updates` : "Order updates"}
          tone={latestReference ? "success" : "info"}
        />

        {statusTimeline.length || trackingReferences.length ? (
          <div className="order-status-timeline">
            <div className="order-status-timeline__head">
              <MaterialIcon name="route" size={18} />
              <strong>Status timeline</strong>
            </div>
            {statusTimeline.slice(0, 5).map((event, index) => (
              <div className="order-status-timeline__row" key={`${event.status || event.new_status || "status"}-${index}`}>
                <span />
                <strong>{event.status || event.new_status || "Order update"}</strong>
                <small>{formatDate(event.date_created || event.date, { time: true })}</small>
              </div>
            ))}
            {trackingReferences.map((group) => (
              <div className="order-status-timeline__row order-status-timeline__row--tracking" key={group.id || group.reference}>
                <span />
                <strong>{group.partner}</strong>
                <small>{group.status} · Tracking {group.reference}</small>
              </div>
            ))}
          </div>
        ) : null}
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
          {(order.lines || []).map((line, index) => {
            const resolvedProductId = productId({ ...line, product: line.product || {} });
            const imageUrl = productImageUrl({ ...line, product: line.product || {} });
            const title = productTitle({ ...line, product: line.product || {} });
            return (
              <Link className="order-line-card" to={resolvedProductId ? `/products/${resolvedProductId}` : "/catalog"} key={line.id || index}>
                {imageUrl ? (
                  <img src={imageUrl} alt={title} />
                ) : (
                  <span className="order-line-card__image-fallback">{productInitials(title)}</span>
                )}
                <span>
                  <strong>{title}</strong>
                  <small>Qty {line.quantity}</small>
                </span>
                <em>{formatCurrency(line.line_price_incl_tax ?? line.line_total ?? line.total_incl_tax ?? line.price_incl_tax, line.currency || order.currency)}</em>
              </Link>
            );
          })}
        </div>
      </section>
    </article>
  );
}
