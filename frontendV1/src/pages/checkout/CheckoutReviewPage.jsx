import { useEffect, useMemo, useState } from "react";
import { Link, Navigate, useLocation, useNavigate, useSearchParams } from "react-router-dom";

import CheckoutStepper from "../../components/checkout/CheckoutStepper.jsx";
import OrderSummaryPanel from "../../components/checkout/OrderSummaryPanel.jsx";
import PaymentProgressPanel from "../../components/payment/PaymentProgressPanel.jsx";
import Alert from "../../components/ui/Alert.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import Spinner from "../../components/ui/Spinner.jsx";
import { useCheckout } from "../../hooks/useCheckout";
import { usePayment } from "../../hooks/usePayment";
import { useUiStore } from "../../store/ui.store";
import { formatCurrency } from "../../utils/currency";
import {
  PAYMENT_CONFIRMATION_TIMEOUT_MS,
  PAYMENT_CONFIRMATION_TIMEOUT_MESSAGE,
  isPaymentComplete,
  isPaymentFailed,
  paymentRequiresPrepayment,
  paymentStatusView,
  readPendingCheckout,
  readablePaymentMethod,
  storePendingCheckout
} from "../../utils/payment";
import { productTitle } from "../../utils/productDisplay";
import "./CheckoutFlow.css";

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
  const [searchParams] = useSearchParams();
  const notify = useUiStore((state) => state.notify);
  const [pending] = useState(() => location.state?.reviewPayload || readPendingCheckout(searchParams));
  const { loading, saving, error, previewCheckout, placeOrder } = useCheckout({ auto: false });
  const paymentState = usePayment({ auto: false });
  const [preview, setPreview] = useState(null);
  const [verifiedPayment, setVerifiedPayment] = useState(pending?.payment || null);
  const [checkingStatus, setCheckingStatus] = useState(false);
  const [confirmationStartedAt, setConfirmationStartedAt] = useState(() => pending?.payment && !isPaymentComplete(pending.payment) ? Date.now() : null);
  const [clockTick, setClockTick] = useState(() => Date.now());

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

  useEffect(() => {
    if (pending?.payment?.method !== "pesapal" || !pending?.payment_reference || isPaymentComplete(pending.payment)) return;

    let active = true;
    const startedAt = Date.now();
    setConfirmationStartedAt(startedAt);
    setClockTick(startedAt);
    paymentState.waitForPayment(pending.payment, {
      maxPolls: 80,
      delayMs: 3000,
      timeoutMs: PAYMENT_CONFIRMATION_TIMEOUT_MS,
      onUpdate: (nextPayment) => {
        if (!active || !nextPayment) return;
        setVerifiedPayment(nextPayment);
        storePendingCheckout({ ...pending, payment: nextPayment });
      }
    })
      .then((nextPayment) => {
        if (!active) return;
        setVerifiedPayment(nextPayment);
        setConfirmationStartedAt(null);
        storePendingCheckout({ ...pending, payment: nextPayment });
      })
      .catch(() => {});

    return () => {
      active = false;
    };
  }, [pending, paymentState.waitForPayment]);

  useEffect(() => {
    if (!confirmationStartedAt || isPaymentComplete(verifiedPayment) || isPaymentFailed(verifiedPayment)) return undefined;
    const timer = window.setInterval(() => setClockTick(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, [confirmationStartedAt, verifiedPayment]);

  const shipping = useMemo(() => previewShipping(preview), [preview]);
  const address = preview?.shipping?.address;
  const payment = verifiedPayment || pending?.payment;
  const methodName = pending?.method?.name || readablePaymentMethod(payment?.method);
  const paymentView = paymentStatusView(payment);
  const requiresPrepayment = paymentRequiresPrepayment(pending?.method || payment?.method);
  const paymentReady = !requiresPrepayment || isPaymentComplete(payment);
  const visiblePaymentError = paymentState.error === PAYMENT_CONFIRMATION_TIMEOUT_MESSAGE ? "" : paymentState.error;
  const elapsedMs = confirmationStartedAt ? Math.max(0, clockTick - confirmationStartedAt) : 0;
  const paymentTimedOut = Boolean(
    requiresPrepayment &&
      payment &&
      confirmationStartedAt &&
      elapsedMs >= PAYMENT_CONFIRMATION_TIMEOUT_MS &&
      !isPaymentComplete(payment) &&
      !isPaymentFailed(payment)
  );
  const remainingSeconds = confirmationStartedAt && !paymentTimedOut
    ? Math.max(0, Math.ceil((PAYMENT_CONFIRMATION_TIMEOUT_MS - elapsedMs) / 1000))
    : 0;

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
    let paymentForOrder = payment;
    if (requiresPrepayment) {
      setCheckingStatus(true);
      try {
        paymentForOrder = await paymentState.getPaymentStatus(pending.payment_reference, payment?.method);
        setVerifiedPayment(paymentForOrder);
        storePendingCheckout({ ...pending, payment: paymentForOrder });
      } catch {
        return;
      } finally {
        setCheckingStatus(false);
      }

      if (!isPaymentComplete(paymentForOrder)) {
        const latestView = paymentStatusView(paymentForOrder);
        notify({
          tone: isPaymentFailed(paymentForOrder) ? "warning" : "info",
          title: latestView.title,
          message: latestView.message,
          icon: latestView.icon
        });
        return;
      }
    }
    try {
      const orderPayload = await placeOrder({
        payment_reference: paymentForOrder?.reference || pending.payment_reference,
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

  async function handleStatusCheck() {
    if (!pending?.payment_reference) return;
    setCheckingStatus(true);
    try {
      const nextPayment = await paymentState.getPaymentStatus(pending.payment_reference, payment?.method);
      setVerifiedPayment(nextPayment);
      if (isPaymentComplete(nextPayment) || isPaymentFailed(nextPayment)) {
        setConfirmationStartedAt(null);
      }
      storePendingCheckout({ ...pending, payment: nextPayment });
      notify({
        tone: isPaymentComplete(nextPayment) ? "success" : isPaymentFailed(nextPayment) ? "warning" : "info",
        title: paymentStatusView(nextPayment).title,
        message: paymentStatusView(nextPayment).message,
        icon: paymentStatusView(nextPayment).icon
      });
    } catch {
      // Hook state already exposes the normalized message.
    } finally {
      setCheckingStatus(false);
    }
  }

  if (!pending?.payment_reference) return <Navigate to="/checkout/payment" replace />;
  if (loading && !preview) return <Spinner label="Loading order preview" />;
  if (preview?.basket?.is_empty) return <Navigate to="/checkout/cart" replace />;

  return (
    <section className="checkout-page">
      <CheckoutStepper current="review" basket={preview?.basket} shipping={preview?.shipping} pendingCheckout={pending} />

      <div className="checkout-title-row">
        <Link className="back-link" to="/checkout/payment">
          <MaterialIcon name="arrow_back" size={18} /> Payment
        </Link>
        <h1>Review order</h1>
      </div>

      <Alert>{error}</Alert>
      <Alert>{visiblePaymentError}</Alert>
      {preview && !preview.ready ? (
        <Alert tone="warning">Some checkout details are missing. Go back and complete delivery before placing the order.</Alert>
      ) : null}

      <div className="checkout-layout">
        <div className="checkout-stack">
          {requiresPrepayment && !paymentReady ? (
            <PaymentProgressPanel
              payment={payment}
              checking={paymentState.processing || checkingStatus}
              timedOut={paymentTimedOut}
              remainingSeconds={remainingSeconds}
              onCheckStatus={() => void handleStatusCheck()}
              onPromptAgain={() => navigate("/checkout/payment")}
              onContinue={() => {}}
              onChangeMethod={() => navigate("/checkout/payment")}
            />
          ) : null}

          <section className="checkout-card review-card">
            <div className="checkout-card__title">
              <span><MaterialIcon name="fact_check" size={20} /></span>
              <div>
                <h2>Confirm details</h2>
              </div>
            </div>

            <div className="review-grid">
              <div>
                <span>Payment</span>
                <strong>{methodName}</strong>
                <small>{paymentView.label}</small>
              </div>
              <div>
                <span>Delivery method</span>
                <strong>{preview?.shipping?.selected_method?.name || "Selected"}</strong>
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
              </div>
            </div>

            <div className="review-lines">
              {(preview?.basket?.lines || []).map((line) => (
                <div className="review-line" key={line.id}>
                  <span>{line.quantity}x</span>
                  <strong>{productTitle({ ...line, product: line.product || {} })}</strong>
                  <em>{formatCurrency(line.line_total, line.currency || preview?.basket?.currency)}</em>
                </div>
              ))}
            </div>
          </section>

          <button
            className="primary-button checkout-submit"
            type="button"
            disabled={saving || checkingStatus || !preview?.ready || !paymentReady}
            onClick={() => void handlePlaceOrder()}
          >
            <MaterialIcon name="task_alt" size={19} />
            {saving ? "Placing order..." : checkingStatus ? "Verifying payment..." : paymentReady ? "Place order" : "Waiting for payment"}
          </button>
        </div>

        <OrderSummaryPanel basket={preview?.basket} shipping={shipping} loading={saving} />
      </div>
    </section>
  );
}
