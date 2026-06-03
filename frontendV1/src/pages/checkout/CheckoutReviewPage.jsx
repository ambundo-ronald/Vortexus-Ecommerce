import { useEffect, useMemo, useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";

import CheckoutStepper from "../../components/checkout/CheckoutStepper.jsx";
import OrderSummaryPanel from "../../components/checkout/OrderSummaryPanel.jsx";
import Alert from "../../components/ui/Alert.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import Spinner from "../../components/ui/Spinner.jsx";
import { useCheckout } from "../../hooks/useCheckout";
import { paymentsApi } from "../../api/payments.api";
import { useUiStore } from "../../store/ui.store";
import { formatCurrency } from "../../utils/currency";
import "./CheckoutFlow.css";

function readPendingCheckout() {
  try {
    return JSON.parse(sessionStorage.getItem("vortexus:pendingCheckout") || "null");
  } catch {
    return null;
  }
}

function previewShipping(preview) {
  const shipping = preview?.shipping || {};
  const totals = preview?.totals || shipping.totals || {};
  return {
    ...shipping,
    totals: {
      ...(shipping.totals || {}),
      shipping: totals.shipping ?? shipping.totals?.shipping ?? 0,
      tax: totals.taxes?.total_tax ?? totals.tax ?? shipping.totals?.tax ?? 0,
      order_total: totals.order_total ?? shipping.totals?.order_total ?? preview?.basket?.totals?.subtotal ?? 0,
      currency: totals.currency || shipping.totals?.currency || preview?.basket?.currency
    }
  };
}

export default function CheckoutReviewPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const notify = useUiStore((state) => state.notify);
  const pending = location.state?.reviewPayload || readPendingCheckout();
  const { loading, saving, error, previewCheckout, placeOrder } = useCheckout({ auto: false });
  const [preview, setPreview] = useState(null);

  useEffect(() => {
    let active = true;
    previewCheckout()
      .then((payload) => {
        if (!active) return;
        setPreview(payload);
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, [previewCheckout]);

  const shipping = useMemo(() => previewShipping(preview), [preview]);
  const address = preview?.shipping?.address;
  const payment = pending?.payment;
  const methodName = pending?.method?.name || readablePayment(payment?.method);

  async function handlePlaceOrder() {
    if (!preview?.ready) {
      notify({
        tone: "warning",
        title: "Checkout is incomplete",
        message: "Confirm delivery details before placing this order.",
        icon: "info"
      });
      navigate("/checkout/shipping");
      return;
    }
    try {
      let paymentReference = pending.payment_reference;
      if (pending?.payment?.method === "pesapal") {
        const statusPayload = await paymentsApi.pesapalStatus(pending.payment_reference);
        const verifiedPayment = statusPayload?.payment;
        if (!["authorized", "paid"].includes(verifiedPayment?.status)) {
          notify({
            tone: "warning",
            title: "Payment not verified",
            message: "Pesapal has not confirmed this payment yet.",
            icon: "hourglass_top"
          });
          return;
        }
        paymentReference = verifiedPayment.reference;
      }
      const orderPayload = await placeOrder({
        payment_reference: paymentReference,
        guest_email: pending.guest_email
      });
      sessionStorage.removeItem("vortexus:pendingCheckout");
      sessionStorage.setItem("vortexus:lastOrder", JSON.stringify(orderPayload));
      const orderNumber = orderPayload?.order?.number || orderPayload?.order?.order_number;
      notify({ title: "Order placed", message: "Your order has been received.", icon: "task_alt" });
      navigate(`/checkout/confirmation${orderNumber ? `?order_number=${encodeURIComponent(orderNumber)}` : ""}`, { replace: true, state: { orderPayload } });
    } catch {
      // Hook state already exposes the normalized message.
    }
  }

  if (!pending?.payment_reference) return <Navigate to="/checkout/payment" replace />;
  if (loading && !preview) return <Spinner label="Loading order preview" />;
  if (preview?.basket?.is_empty) return <Navigate to="/checkout/cart" replace />;

  return (
    <section className="checkout-page">
      <CheckoutStepper current="review" />

      <div className="checkout-title-row">
        <Link className="back-link" to="/checkout/payment">
          <MaterialIcon name="arrow_back" size={18} /> Payment
        </Link>
        <h1>Review order</h1>
      </div>

      <Alert>{error}</Alert>
      {preview && !preview.ready ? (
        <Alert tone="warning">Some checkout details are missing. Go back and complete delivery before placing the order.</Alert>
      ) : null}

      <div className="checkout-layout">
        <div className="checkout-stack">
          <section className="checkout-card review-card">
            <div className="checkout-card__title">
              <span><MaterialIcon name="fact_check" size={20} /></span>
              <div>
                <h2>Confirm details</h2>
                <p>Check delivery, payment, and items before placing the order.</p>
              </div>
            </div>

            <div className="review-grid">
              <div>
                <span>Payment</span>
                <strong>{methodName}</strong>
                <small>{payment?.status || "Ready"}</small>
              </div>
              <div>
                <span>Delivery method</span>
                <strong>{preview?.shipping?.selected_method?.name || "Selected"}</strong>
                <small>{preview?.shipping?.selected_method?.description || "Saved delivery option"}</small>
              </div>
              <div>
                <span>Delivery address</span>
                <strong>{address ? [address.line1, address.line4].filter(Boolean).join(", ") : "Saved"}</strong>
                <small>{address ? [address.postcode, address.country_code].filter(Boolean).join(", ") : ""}</small>
              </div>
            </div>
          </section>

          <section className="checkout-card review-card">
            <div className="checkout-card__title">
              <span><MaterialIcon name="inventory_2" size={20} /></span>
              <div>
                <h2>Items</h2>
                <p>{preview?.basket?.item_count || 0} item{preview?.basket?.item_count === 1 ? "" : "s"} in this order.</p>
              </div>
            </div>

            <div className="review-lines">
              {(preview?.basket?.lines || []).map((line) => (
                <div className="review-line" key={line.id}>
                  <span>{line.quantity}x</span>
                  <strong>{line.product?.title || "Product"}</strong>
                  <em>{formatCurrency(line.line_total, line.currency || preview?.basket?.currency)}</em>
                </div>
              ))}
            </div>
          </section>

          <button className="primary-button checkout-submit" type="button" disabled={saving || !preview?.ready} onClick={() => void handlePlaceOrder()}>
            <MaterialIcon name="task_alt" size={19} />
            {saving ? "Placing order..." : "Place order"}
          </button>
        </div>

        <OrderSummaryPanel basket={preview?.basket} shipping={shipping} loading={saving} />
      </div>
    </section>
  );
}

function readablePayment(method = "") {
  return method.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase()) || "Payment";
}
