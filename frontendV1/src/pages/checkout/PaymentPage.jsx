import { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";

import CheckoutErrorAlert from "../../components/checkout/CheckoutErrorAlert.jsx";
import CheckoutStepper from "../../components/checkout/CheckoutStepper.jsx";
import OrderSummaryPanel from "../../components/checkout/OrderSummaryPanel.jsx";
import PaymentMethodSelector from "../../components/checkout/PaymentMethodSelector.jsx";
import PaymentProgressPanel from "../../components/payment/PaymentProgressPanel.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import Spinner from "../../components/ui/Spinner.jsx";
import { useCheckout } from "../../hooks/useCheckout";
import { usePayment } from "../../hooks/usePayment";
import { useAuthStore } from "../../store/auth.store";
import { useUiStore } from "../../store/ui.store";
import {
  isPaymentComplete,
  isPaymentFailed,
  paymentRequiresPrepayment,
  storePendingCheckout
} from "../../utils/payment";
import { checkoutToastPayload } from "../../utils/checkoutErrors";
import "./CheckoutFlow.css";

export default function PaymentPage() {
  const navigate = useNavigate();
  const checkoutState = useCheckout();
  const paymentState = usePayment();
  const user = useAuthStore((state) => state.user);
  const notify = useUiStore((state) => state.notify);
  const { basket, shipping, loading, saving, error, errorView, previewCheckout } = checkoutState;
  const paymentError = paymentState.error;
  const paymentErrorView = paymentState.errorView;
  const [activePayment, setActivePayment] = useState(null);
  const [activeMethod, setActiveMethod] = useState(null);
  const [guestEmail, setGuestEmail] = useState("");
  const [checkingStatus, setCheckingStatus] = useState(false);

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

      const finalPayment = await paymentState.waitForPayment(payment, {
        onUpdate: (nextPayment) => {
          if (!nextPayment) return;
          setActivePayment(nextPayment);
          storePendingCheckout({ ...reviewPayload, payment: nextPayment });
        }
      });
      setActivePayment(finalPayment);
      continueToReview(finalPayment, selectedMethod, form.payerEmail);
    } catch (error) {
      const context = error?.message?.toLowerCase?.().includes("pending") ? "payment_status" : "payment";
      notify(checkoutToastPayload(error, context));
    }
  }

  async function handleStatusCheck() {
    if (!activePayment?.reference) return;
    setCheckingStatus(true);
    try {
      const nextPayment = await paymentState.getPaymentStatus(activePayment.reference, activePayment.method);
      setActivePayment(nextPayment);
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
    } catch (error) {
      notify(checkoutToastPayload(error, "payment_status"));
    } finally {
      setCheckingStatus(false);
    }
  }

  function handleChangeMethod() {
    setActivePayment(null);
    setActiveMethod(null);
    paymentState.clearError();
  }

  if (loading || paymentState.loading) return <Spinner label="Loading payment" />;
  if (!loading && basket?.is_empty) return <Navigate to="/checkout/cart" replace />;
  if (!loading && shipping && !shipping.ready_for_checkout) return <Navigate to="/checkout/shipping" replace />;

  return (
    <section className="checkout-page">
      <CheckoutStepper current="payment" basket={basket} shipping={shipping} />

      <CheckoutErrorAlert error={paymentErrorView || errorView} fallback={paymentError || error} />

      <div className="checkout-layout">
        <div className="checkout-stack">
          {activePayment ? (
            <PaymentProgressPanel
              payment={activePayment}
              checking={paymentState.processing || checkingStatus}
              onCheckStatus={() => void handleStatusCheck()}
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
