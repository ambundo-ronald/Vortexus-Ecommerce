import { Link, Navigate, useNavigate } from "react-router-dom";

import CheckoutStepper from "../../components/checkout/CheckoutStepper.jsx";
import OrderSummaryPanel from "../../components/checkout/OrderSummaryPanel.jsx";
import PaymentMethodSelector from "../../components/checkout/PaymentMethodSelector.jsx";
import Alert from "../../components/ui/Alert.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import Spinner from "../../components/ui/Spinner.jsx";
import { useCheckout } from "../../hooks/useCheckout";
import { usePayment } from "../../hooks/usePayment";
import { useUiStore } from "../../store/ui.store";

const COMPLETE_STATUSES = new Set(["authorized", "paid"]);

export default function PaymentPage() {
  const navigate = useNavigate();
  const checkoutState = useCheckout();
  const paymentState = usePayment();
  const notify = useUiStore((state) => state.notify);
  const { basket, shipping, loading, saving, error, placeOrder } = checkoutState;
  const paymentError = paymentState.error;

  async function handlePaymentSubmit(form) {
    try {
      const payment = await paymentState.initializePayment(form);
      const selectedMethod = paymentState.methods.find((method) => method.code === payment.method);
      const finalPayment = selectedMethod?.requires_prepayment && !COMPLETE_STATUSES.has(payment.status)
        ? await paymentState.waitForPayment(payment)
        : payment;
      const orderPayload = await placeOrder({
        payment_reference: finalPayment.reference,
        guest_email: form.payerEmail
      });
      sessionStorage.setItem("vortexus:lastOrder", JSON.stringify(orderPayload));
      notify({ title: "Order placed", message: "Your order has been received.", icon: "task_alt" });
      navigate("/checkout/confirmation", { replace: true, state: { orderPayload } });
    } catch {
      // Hook state already exposes the normalized message.
    }
  }

  if (loading || paymentState.loading) return <Spinner label="Loading payment" />;
  if (!loading && basket?.is_empty) return <Navigate to="/checkout/cart" replace />;
  if (!loading && shipping && !shipping.ready_for_checkout) return <Navigate to="/checkout/shipping" replace />;

  return (
    <section className="checkout-page">
      <CheckoutStepper current="payment" />

      <div className="checkout-title-row">
        <Link className="back-link" to="/checkout/shipping">
          <MaterialIcon name="arrow_back" size={18} /> Delivery
        </Link>
        <h1>Payment</h1>
      </div>

      <Alert>{error || paymentError}</Alert>
      {paymentError ? (
        <Alert tone="warning">Choose another payment option if this one is not available.</Alert>
      ) : null}
      {paymentState.payment?.status === "pending" ? (
        <Alert tone="info">Payment request sent. Approve the prompt on your phone to place the order.</Alert>
      ) : null}

      <div className="checkout-layout">
        <div className="checkout-stack">
          <PaymentMethodSelector
            methods={paymentState.methods}
            processing={paymentState.processing || saving}
            onSubmit={handlePaymentSubmit}
          />
        </div>
        <OrderSummaryPanel basket={basket} shipping={shipping} loading={paymentState.processing || saving} />
      </div>
    </section>
  );
}
