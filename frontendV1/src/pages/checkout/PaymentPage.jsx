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

export default function PaymentPage() {
  const navigate = useNavigate();
  const checkoutState = useCheckout();
  const paymentState = usePayment();
  const notify = useUiStore((state) => state.notify);
  const { basket, shipping, loading, saving, error, previewCheckout, placeOrder } = checkoutState;
  const paymentError = paymentState.error;

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
      const payment = await paymentState.initializePayment(form);
      const orderPayload = await placeOrder({
        payment_reference: payment.reference,
        guest_email: form.payerEmail
      });
      sessionStorage.setItem("vortexus:lastOrder", JSON.stringify(orderPayload));
      const orderNumber = orderPayload?.order?.number || orderPayload?.order?.order_number;
      notify({ title: "Order placed", message: "Your order has been received.", icon: "task_alt" });
      navigate(`/checkout/confirmation${orderNumber ? `?order_number=${encodeURIComponent(orderNumber)}` : ""}`, { replace: true, state: { orderPayload } });
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
