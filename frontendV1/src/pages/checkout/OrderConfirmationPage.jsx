import { Link, useLocation } from "react-router-dom";

import CheckoutStepper from "../../components/checkout/CheckoutStepper.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import { formatCurrency } from "../../utils/currency";

function readStoredOrder() {
  try {
    return JSON.parse(sessionStorage.getItem("vortexus:lastOrder") || "null");
  } catch {
    return null;
  }
}

export default function OrderConfirmationPage() {
  const location = useLocation();
  const payload = location.state?.orderPayload || readStoredOrder();
  const order = payload?.order;
  const payment = payload?.payment;
  const address = order?.shipping_address;

  if (!order) {
    return (
      <section className="checkout-page">
        <CheckoutStepper current="done" />
        <div className="checkout-card confirmation-card">
          <span className="confirmation-icon muted">
            <MaterialIcon name="receipt_long" size={30} />
          </span>
          <h1>No recent order</h1>
          <p>Once an order is placed, its confirmation will appear here.</p>
          <Link className="primary-button" to="/catalog">
            <MaterialIcon name="storefront" size={19} />
            Continue shopping
          </Link>
        </div>
      </section>
    );
  }

  return (
    <section className="checkout-page">
      <CheckoutStepper current="done" />

      <div className="checkout-card confirmation-card">
        <span className="confirmation-icon">
          <MaterialIcon name="check_circle" size={34} />
        </span>
        <h1>Order placed</h1>
        <p>Order #{order.number || order.order_number} is now in progress.</p>

        <div className="confirmation-grid">
          <div>
            <span>Total</span>
            <strong>{formatCurrency(order.totals?.total_incl_tax || order.total_incl_tax || order.total || order.order_total, order.currency || "USD")}</strong>
          </div>
          <div>
            <span>Payment</span>
            <strong>{payment?.status || "received"}</strong>
          </div>
          <div>
            <span>Method</span>
            <strong>{readablePayment(payment?.method)}</strong>
          </div>
          <div>
            <span>Delivery</span>
            <strong>{address?.line4 || order.shipping_method || "Saved"}</strong>
          </div>
        </div>

        {address ? (
          <div className="confirmation-address">
            <MaterialIcon name="location_on" size={18} />
            <span>{[address.line1, address.line2, address.line4, address.country_code].filter(Boolean).join(", ")}</span>
          </div>
        ) : null}

        <Link className="primary-button" to="/catalog">
          <MaterialIcon name="storefront" size={19} />
          Continue shopping
        </Link>
      </div>
    </section>
  );
}

function readablePayment(method = "") {
  return method.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase()) || "Payment";
}
