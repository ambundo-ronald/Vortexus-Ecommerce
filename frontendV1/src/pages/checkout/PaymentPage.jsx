import { useEffect, useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";

import CheckoutStepper from "../../components/checkout/CheckoutStepper.jsx";
import OrderSummaryPanel from "../../components/checkout/OrderSummaryPanel.jsx";
import PaymentMethodSelector from "../../components/checkout/PaymentMethodSelector.jsx";
import PaymentProgressPanel from "../../components/payment/PaymentProgressPanel.jsx";
import Alert from "../../components/ui/Alert.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import Spinner from "../../components/ui/Spinner.jsx";
import { useCheckout } from "../../hooks/useCheckout";
import { usePayment } from "../../hooks/usePayment";
import { useAuthStore } from "../../store/auth.store";
import { useUiStore } from "../../store/ui.store";
import {
  PAYMENT_CONFIRMATION_TIMEOUT_MS,
  isPaymentComplete,
  isPaymentFailed,
  paymentRequiresPrepayment,
  storePendingCheckout
} from "../../utils/payment";
import "./CheckoutFlow.css";

export default function PaymentPage() {
  const navigate = useNavigate();
  const checkoutState = useCheckout();
  const paymentState = usePayment();
  const user = useAuthStore((state) => state.user);
  const notify = useUiStore((state) => state.notify);
  const { basket, shipping, loading, saving, error, previewCheckout } = checkoutState;
  const paymentError = paymentState.error;
  const [activePayment, setActivePayment] = useState(null);
  const [activeMethod, setActiveMethod] = useState(null);
  const [guestEmail, setGuestEmail] = useState("");
  const [checkingStatus, setCheckingStatus] = useState(false);
  const [lastPaymentForm, setLastPaymentForm] = useState(null);
  const [confirmationStartedAt, setConfirmationStartedAt] = useState(null);
  const [clockTick, setClockTick] = useState(() => Date.now());

  const elapsedMs = confirmationStartedAt ? Math.max(0, clockTick - confirmationStartedAt) : 0;
  const paymentTimedOut = Boolean(
    activePayment &&
      confirmationStartedAt &&
      elapsedMs >= PAYMENT_CONFIRMATION_TIMEOUT_MS &&
      !isPaymentComplete(activePayment) &&
      !isPaymentFailed(activePayment)
  );
  const remainingSeconds = confirmationStartedAt && !paymentTimedOut
    ? Math.max(0, Math.ceil((PAYMENT_CONFIRMATION_TIMEOUT_MS - elapsedMs) / 1000))
    : 0;

  useEffect(() => {
    if (!activePayment || !confirmationStartedAt || isPaymentComplete(activePayment) || isPaymentFailed(activePayment)) return undefined;
    const timer = window.setInterval(() => setClockTick(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, [activePayment, confirmationStartedAt]);

  function continueToReview(payment, method, payerEmail) {
    const reviewPayload = {
      payment_reference: payment.reference,
      payment,
      method: method || null,
      guest_email: payerEmail
    };
    storePendingCheckout(reviewPayload);
    notify({ title: "Ready to review", message: "Confirm the order details before placing it.", icon: "fact_check" });
    navigate("/checkout/review", { state: { reviewPayload } });
  }

  async function handlePaymentSubmit(form) {
    setLastPaymentForm(form);
    setConfirmationStartedAt(null);
    setClockTick(Date.now());
    try {
      const preview = await previewCheckout();
      if (preview && !preview.ready) {
        const missing = preview.missing || [];
        notify({
          tone: "warning",
          title: "Checkout needs one more step",
          message: missing.includes("shipping_address") ? "Add a delivery address before placing the order." : "Select a delivery method before placing the order.",
          icon: "info"
        });
        navigate("/checkout/shipping");
        return;
      }
      const payment = await paymentState.initializePayment({
        ...form,
        customerName: [user?.first_name, user?.last_name].filter(Boolean).join(" ")
      });
      const selectedMethod = paymentState.methods.find((method) => method.code === payment.method);
      setActivePayment(payment);
      setActiveMethod(selectedMethod || null);
      setGuestEmail(form.payerEmail);

      const reviewPayload = {
        payment_reference: payment.reference,
        payment,
        method: selectedMethod || null,
        guest_email: form.payerEmail
      };
      storePendingCheckout(reviewPayload);

      if (payment.method === "pesapal" && payment.redirect_url) {
        window.location.assign(payment.redirect_url);
        return;
      }

      if (!paymentRequiresPrepayment(selectedMethod) || isPaymentComplete(payment)) {
        continueToReview(payment, selectedMethod, form.payerEmail);
        return;
      }

      const startedAt = Date.now();
      setConfirmationStartedAt(startedAt);
      setClockTick(startedAt);
      const finalPayment = await paymentState.waitForPayment(payment, {
        timeoutMs: PAYMENT_CONFIRMATION_TIMEOUT_MS,
        onUpdate: (nextPayment) => {
          if (!nextPayment) return;
          setActivePayment(nextPayment);
          storePendingCheckout({ ...reviewPayload, payment: nextPayment });
        }
      });
      setActivePayment(finalPayment);
      continueToReview(finalPayment, selectedMethod, form.payerEmail);
    } catch {
      // Hook state already exposes the normalized message.
    }
  }

  async function handleStatusCheck() {
    if (!activePayment?.reference) return;
    setCheckingStatus(true);
    try {
      const nextPayment = await paymentState.getPaymentStatus(activePayment.reference, activePayment.method);
      setActivePayment(nextPayment);
      if (isPaymentComplete(nextPayment) || isPaymentFailed(nextPayment)) {
        setConfirmationStartedAt(null);
      }
      storePendingCheckout({
        payment_reference: nextPayment.reference,
        payment: nextPayment,
        method: activeMethod,
        guest_email: guestEmail
      });
      if (isPaymentComplete(nextPayment)) {
        notify({ title: "Payment confirmed", message: "Your payment is ready for order review.", icon: "check_circle" });
      } else if (isPaymentFailed(nextPayment)) {
        notify({ tone: "warning", title: "Payment not completed", message: "Retry or choose another payment method.", icon: "error" });
      }
    } catch {
      // Hook state already exposes the normalized message.
    } finally {
      setCheckingStatus(false);
    }
  }

  function handleChangeMethod() {
    setActivePayment(null);
    setActiveMethod(null);
    setConfirmationStartedAt(null);
    setClockTick(Date.now());
    paymentState.setError("");
  }

  async function handlePromptAgain() {
    if (!lastPaymentForm) {
      handleChangeMethod();
      return;
    }
    setActivePayment(null);
    setActiveMethod(null);
    setConfirmationStartedAt(null);
    setClockTick(Date.now());
    paymentState.setError("");
    notify({ title: "Sending a fresh prompt", message: "Check your phone for the new payment prompt.", icon: "phone_iphone" });
    await handlePaymentSubmit(lastPaymentForm);
  }

  if (loading || paymentState.loading) return <Spinner label="Loading payment" />;
  if (!loading && basket?.is_empty) return <Navigate to="/checkout/cart" replace />;
  if (!loading && shipping && !shipping.ready_for_checkout) return <Navigate to="/checkout/shipping" replace />;

  return (
    <section className="checkout-page">
      <CheckoutStepper current="payment" basket={basket} shipping={shipping} />

      <div className="checkout-title-row">
        <Link className="back-link" to="/checkout/shipping">
          <MaterialIcon name="arrow_back" size={18} /> Delivery
        </Link>
        <h1>Payment</h1>
      </div>

      <Alert>{error || paymentError}</Alert>

      <div className="checkout-layout">
        <div className="checkout-stack">
          {activePayment ? (
            <PaymentProgressPanel
              payment={activePayment}
              checking={paymentState.processing || checkingStatus}
              timedOut={paymentTimedOut}
              remainingSeconds={remainingSeconds}
              onCheckStatus={() => void handleStatusCheck()}
              onPromptAgain={() => void handlePromptAgain()}
              onContinue={() => continueToReview(activePayment, activeMethod, guestEmail)}
              onChangeMethod={handleChangeMethod}
            />
          ) : (
            <PaymentMethodSelector
              methods={paymentState.methods}
              processing={paymentState.processing || saving}
              onSubmit={handlePaymentSubmit}
              submitLabel="Continue securely"
              defaultEmail={user?.email || ""}
              defaultPhone={user?.phone || user?.phone_number || ""}
            />
          )}
        </div>
        <OrderSummaryPanel basket={basket} shipping={shipping} loading={paymentState.processing || saving} />
      </div>
    </section>
  );
}
