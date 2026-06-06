import { useEffect, useState } from "react";
import { Link, useLocation, useSearchParams } from "react-router-dom";

import CheckoutStepper from "../../components/checkout/CheckoutStepper.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import Spinner from "../../components/ui/Spinner.jsx";
import Alert from "../../components/ui/Alert.jsx";
import { useCheckout } from "../../hooks/useCheckout";
import { trackStorefrontEvent } from "../../utils/analytics";
import { formatCurrency } from "../../utils/currency";
import "./CheckoutFlow.css";

function readStoredOrder() {
  try {
    return JSON.parse(sessionStorage.getItem("vortexus:lastOrder") || "null");
  } catch {
    return null;
  }
}

export default function OrderConfirmationPage() {
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const storedPayload = location.state?.orderPayload || readStoredOrder();
  const [payload, setPayload] = useState(storedPayload);
  const { loading, error, loadOrderConfirmation } = useCheckout({ auto: false });
  const orderNumber = searchParams.get("order_number") || storedPayload?.order?.number || storedPayload?.order?.order_number || "";

  useEffect(() => {
    if (!orderNumber) return;
    let active = true;
    loadOrderConfirmation(orderNumber)
      .then((response) => {
        if (!active) return;
        setPayload(response);
        sessionStorage.setItem("vortexus:lastOrder", JSON.stringify(response));
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, [loadOrderConfirmation, orderNumber]);

  const order = payload?.order;
  const payment = payload?.payment;
  const address = order?.shipping_address;
  const lines = order?.lines || [];

  useEffect(() => {
    if (!order) return;
    trackStorefrontEvent("order_confirmation_viewed", {
      order_number: order.number || order.order_number,
      currency: order.currency || "KES",
      total: order.totals?.total_incl_tax || order.total_incl_tax || order.total || order.order_total
    });
  }, [order]);

  if (loading && !order) return <Spinner label="Loading order confirmation" />;

  if (!order) {
    return (
      <section className="checkout-page">
        <CheckoutStepper current="done" />
        <div className="checkout-card confirmation-card">
          <span className="confirmation-icon muted">
            <MaterialIcon name="receipt_long" size={30} />
          </span>
          <h1>No recent order</h1>
          <Alert>{error}</Alert>
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

      <div className="checkout-card confirmation-card printable-order-summary">
        <span className="confirmation-icon">
          <MaterialIcon name="check_circle" size={34} />
        </span>
        <h1>Order placed</h1>
        <p>Order #{order.number || order.order_number} is now in progress.</p>

        <div className="confirmation-grid">
          <div>
            <span>Total</span>
            <strong>{formatCurrency(order.totals?.total_incl_tax || order.total_incl_tax || order.total || order.order_total, order.currency || "KES")}</strong>
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

        {lines.length ? (
          <div className="confirmation-lines">
            <h2>Items</h2>
            {lines.map((line) => (
              <div className="confirmation-line" key={line.id}>
                <span>{line.quantity}x</span>
                <strong>
                  {line.title || "Product"}
                  {line.options?.length ? (
                    <small>{line.options.map((option) => `${option.name || option.code}: ${option.value}`).join(" / ")}</small>
                  ) : null}
                </strong>
                <em>{formatCurrency(line.line_price_incl_tax, line.currency || order.currency || "KES")}</em>
              </div>
            ))}
          </div>
        ) : null}

        <div className="confirmation-actions no-print">
          <button className="secondary-button" type="button" onClick={() => window.print()}>
            <MaterialIcon name="print" size={19} />
            Print summary
          </button>
          <Link className="primary-button" to="/catalog">
            <MaterialIcon name="storefront" size={19} />
            Continue shopping
          </Link>
        </div>
      </div>
    </section>
  );
}

function readablePayment(method = "") {
  return method.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase()) || "Payment";
}
