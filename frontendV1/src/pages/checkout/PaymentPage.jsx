import { useEffect, useRef, useState } from "react";
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
import { trackStorefrontEvent } from "../../utils/analytics";
import {
  PAYMENT_CONFIRMATION_TIMEOUT_MS,
  PAYMENT_CONFIRMATION_TIMEOUT_MESSAGE,
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
  const visiblePaymentError = paymentError === PAYMENT_CONFIRMATION_TIMEOUT_MESSAGE ? "" : paymentError;
  const [activePayment, setActivePayment] = useState(null);
  const [activeMethod, setActiveMethod] = useState(null);
  const [guestEmail, setGuestEmail] = useState("");
  const [checkingStatus, setCheckingStatus] = useState(false);
  const [lastPaymentForm, setLastPaymentForm] = useState(null);
  const [confirmationStartedAt, setConfirmationStartedAt] = useState(null);
  const [clockTick, setClockTick] = useState(() => Date.now());
  const paymentStartedRef = useRef(false);
  const timeoutTrackedRef = useRef("");

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
  const userPaymentStateKey = [
    user?.id || "guest",
    user?.cash_on_delivery_allowed ? "cod-allowed" : "cod-default",
    user?.payment_permissions?.cash_on_delivery_available ? "cod-available" : "cod-unavailable"
  ].join(":");

  function paymentMetadata(extra = {}) {
    return {
      item_count: basket?.item_count || basket?.lines?.length || 0,
      line_count: basket?.lines?.length || 0,
      currency: shipping?.totals?.currency || basket?.currency || "",
      shipping_method: shipping?.selected_method?.code || "",
      shipping_method_name: shipping?.selected_method?.name || "",
      payment_method: activePayment?.method || activeMethod?.code || lastPaymentForm?.method || "",
      payment_status: activePayment?.status || "",
      payment_reference: activePayment?.reference || "",
      provider_reference: activePayment?.provider_reference || "",
      order_total: shipping?.totals?.order_total ?? basket?.totals?.order_total,
      requires_prepayment: activeMethod ? paymentRequiresPrepayment(activeMethod) : undefined,
      remaining_seconds: remainingSeconds,
      ...extra
    };
  }

  useEffect(() => {
    if (!activePayment || !confirmationStartedAt || isPaymentComplete(activePayment) || isPaymentFailed(activePayment)) return undefined;
    const timer = window.setInterval(() => setClockTick(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, [activePayment, confirmationStartedAt]);

  useEffect(() => {
    if (loading || paymentState.loading || paymentStartedRef.current) return;
    paymentStartedRef.current = true;
    trackStorefrontEvent("payment_started", paymentMetadata());
  }, [loading, paymentState.loading]);

  useEffect(() => {
    if (!paymentTimedOut || !activePayment?.reference || timeoutTrackedRef.current === activePayment.reference) return;
    timeoutTrackedRef.current = activePayment.reference;
    trackStorefrontEvent("payment_timeout", paymentMetadata({
      payment_method: activePayment.method,
      payment_status: activePayment.status,
      payment_reference: activePayment.reference,
      provider_reference: activePayment.provider_reference
    }));
  }, [activePayment, paymentTimedOut]);

  useEffect(() => {
    void paymentState.loadMethods();
  }, [paymentState.loadMethods, userPaymentStateKey]);

  function continueToReview(payment, method, payerEmail) {
    trackStorefrontEvent("payment_continue_to_review", paymentMetadata({
      payment_method: payment?.method || method?.code || "",
      payment_status: payment?.status || "",
      payment_reference: payment?.reference || "",
      provider_reference: payment?.provider_reference || "",
      requires_prepayment: paymentRequiresPrepayment(method || payment?.method)
    }));
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
    trackStorefrontEvent("payment_method_selected", paymentMetadata({
      payment_method: form?.method || "",
      source: "payment_form"
    }));
    try {
      const preview = await previewCheckout();
      if (preview && !preview.ready) {
        const missing = preview.missing || [];
        trackStorefrontEvent("payment_blocked_checkout_incomplete", paymentMetadata({
          payment_method: form?.method || "",
          missing: missing.join(",")
        }));
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
      trackStorefrontEvent(paymentRequiresPrepayment(selectedMethod) ? "payment_prompt_sent" : "payment_initialized", paymentMetadata({
        payment_method: payment.method,
        payment_status: payment.status,
        payment_reference: payment.reference,
        provider_reference: payment.provider_reference,
        requires_prepayment: paymentRequiresPrepayment(selectedMethod)
      }));

      const reviewPayload = {
        payment_reference: payment.reference,
        payment,
        method: selectedMethod || null,
        guest_email: form.payerEmail
      };
      storePendingCheckout(reviewPayload);

      if (payment.method === "pesapal" && payment.redirect_url) {
        trackStorefrontEvent("payment_redirect_started", paymentMetadata({
          payment_method: payment.method,
          payment_status: payment.status,
          payment_reference: payment.reference
        }));
        window.location.assign(payment.redirect_url);
        return;
      }

      if (!paymentRequiresPrepayment(selectedMethod) || isPaymentComplete(payment)) {
        if (isPaymentComplete(payment)) {
          trackStorefrontEvent("payment_confirmed", paymentMetadata({
            payment_method: payment.method,
            payment_status: payment.status,
            payment_reference: payment.reference,
            provider_reference: payment.provider_reference
          }));
        }
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
      trackStorefrontEvent(isPaymentComplete(finalPayment) ? "payment_confirmed" : isPaymentFailed(finalPayment) ? "payment_failed" : "payment_status_checked", paymentMetadata({
        payment_method: finalPayment?.method || payment.method,
        payment_status: finalPayment?.status || "",
        payment_reference: finalPayment?.reference || payment.reference,
        provider_reference: finalPayment?.provider_reference || "",
        remaining_seconds: 0
      }));
      continueToReview(finalPayment, selectedMethod, form.payerEmail);
    } catch {
      trackStorefrontEvent("payment_prompt_failed", paymentMetadata({
        payment_method: form?.method || "",
        reason: "initialize_or_confirm_failed"
      }));
      // Hook state already exposes the normalized message.
    }
  }

  async function handleStatusCheck() {
    if (!activePayment?.reference) return;
    setCheckingStatus(true);
    try {
      const nextPayment = await paymentState.getPaymentStatus(activePayment.reference, activePayment.method);
      setActivePayment(nextPayment);
      trackStorefrontEvent("payment_status_checked", paymentMetadata({
        payment_method: nextPayment?.method || activePayment.method,
        payment_status: nextPayment?.status || "",
        payment_reference: nextPayment?.reference || activePayment.reference,
        provider_reference: nextPayment?.provider_reference || ""
      }));
      if (isPaymentComplete(nextPayment) || isPaymentFailed(nextPayment)) {
        setConfirmationStartedAt(null);
        trackStorefrontEvent(isPaymentComplete(nextPayment) ? "payment_confirmed" : "payment_failed", paymentMetadata({
          payment_method: nextPayment?.method || activePayment.method,
          payment_status: nextPayment?.status || "",
          payment_reference: nextPayment?.reference || activePayment.reference,
          provider_reference: nextPayment?.provider_reference || ""
        }));
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
      trackStorefrontEvent("payment_status_checked", paymentMetadata({
        payment_method: activePayment.method,
        payment_reference: activePayment.reference,
        reason: "status_check_failed"
      }));
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
    trackStorefrontEvent("payment_prompt_retry", paymentMetadata({
      payment_method: lastPaymentForm.method || "",
      source: "timeout_or_manual_retry"
    }));
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

      <Alert>{error || visiblePaymentError}</Alert>

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
