import { Link } from "react-router-dom";

import MaterialIcon from "../ui/MaterialIcon.jsx";
import { basketTaxStatuses, normalizeCheckoutTotals } from "../../utils/checkoutTotals";
import { formatCurrency } from "../../utils/currency";
import { productTitle } from "../../utils/productDisplay";

export default function OrderSummaryPanel({ basket, shipping, action, actionTo, loading = false, whatsappHref = "" }) {
  const totals = normalizeCheckoutTotals({ basket, shipping });
  const lines = basket?.lines || [];
  const currency = totals.currency;
  const subtotal = totals.subtotal;
  const shippingTotal = totals.shipping;
  const tax = totals.tax;
  const orderTotal = totals.order_total;
  const taxStatusLabels = basketTaxStatuses(basket);

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
            <strong>
              {productTitle({ ...line, product: line.product || {} })}
              {line.options?.length ? (
                <small>{line.options.map((option) => `${option.name || option.code}: ${option.value}`).join(" / ")}</small>
              ) : null}
            </strong>
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
              <span>VAT</span>
              <strong>{formatCurrency(tax, currency)}</strong>
            </div>
            {taxStatusLabels.length ? (
              <p className="checkout-tax-note">
                {taxStatusLabels.join(" / ")} item{taxStatusLabels.length === 1 ? "" : "s"} included.
              </p>
            ) : null}
          </>
        ) : (
          <div>
            <span>VAT</span>
            <strong>{formatCurrency(tax, currency)}</strong>
          </div>
        )}
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
      {whatsappHref ? (
        <a className="checkout-whatsapp-button" href={whatsappHref} target="_blank" rel="noreferrer">
          <span className="checkout-whatsapp-button__icon" aria-hidden="true">
            <svg viewBox="0 0 32 32" role="img" focusable="false">
              <path d="M16 3.2A12.7 12.7 0 0 0 5 22.3L3.8 28l5.8-1.5A12.7 12.7 0 1 0 16 3.2Zm0 2.3a10.4 10.4 0 0 1 8.8 15.9 10.4 10.4 0 0 1-14.7 3.2l-.4-.2-3 .8.8-3-.3-.4A10.4 10.4 0 0 1 16 5.5Zm-4.1 5.2c-.3 0-.7.1-1 .5-.4.4-1.3 1.3-1.3 3.1s1.3 3.6 1.5 3.8c.2.3 2.6 4.1 6.4 5.5 3.1 1.2 3.8.9 4.5.8.7-.1 2.2-.9 2.5-1.8.3-.9.3-1.7.2-1.8-.1-.2-.4-.3-.8-.5l-2.4-1.2c-.4-.2-.7-.2-.9.2-.3.4-1 1.2-1.2 1.5-.2.3-.5.3-.9.1-.4-.2-1.6-.6-3-1.9-1.1-1-1.9-2.2-2.1-2.6-.2-.4 0-.6.2-.8l.6-.7c.2-.2.2-.4.4-.7.1-.3.1-.5 0-.7l-1.1-2.6c-.3-.7-.6-.7-.9-.7h-.7Z" />
            </svg>
          </span>
          Buy on WhatsApp
        </a>
      ) : null}
      {loading ? <p className="checkout-note">Updating summary...</p> : null}
    </aside>
  );
}
