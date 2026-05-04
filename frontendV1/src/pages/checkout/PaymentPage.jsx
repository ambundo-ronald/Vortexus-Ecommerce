import { Link, Navigate, useNavigate } from "react-router-dom";

import CheckoutStepper from "../../components/checkout/CheckoutStepper.jsx";
import OrderSummaryPanel from "../../components/checkout/OrderSummaryPanel.jsx";
import PaymentMethodSelector from "../../components/checkout/PaymentMethodSelector.jsx";
import Alert from "../../components/ui/Alert.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import Spinner from "../../components/ui/Spinner.jsx";
import { useCheckout } from "../../hooks/useCheckout";
import { usePayment } from "../../hooks/usePayment";

export default function PaymentPage() {
  const navigate = useNavigate();
  const checkoutState = useCheckout();
  const paymentState = usePayment();
  const { basket, shipping, loading, saving, error, placeOrder } = checkoutState;
  const paymentError = paymentState.error;

  async function handlePaymentSubmit(form) {
    try {
      const payment = await paymentState.initializePayment(form);
      const orderPayload = await placeOrder({
        payment_reference: payment.reference,
        guest_email: form.payerEmail
      });
      sessionStorage.setItem("vortexus:lastOrder", JSON.stringify(orderPayload));
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
