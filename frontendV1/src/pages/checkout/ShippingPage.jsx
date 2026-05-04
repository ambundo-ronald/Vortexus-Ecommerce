import { Link, Navigate, useNavigate } from "react-router-dom";

import CheckoutStepper from "../../components/checkout/CheckoutStepper.jsx";
import OrderSummaryPanel from "../../components/checkout/OrderSummaryPanel.jsx";
import ShippingAddressForm from "../../components/checkout/ShippingAddressForm.jsx";
import ShippingMethodSelector from "../../components/checkout/ShippingMethodSelector.jsx";
import Alert from "../../components/ui/Alert.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import Spinner from "../../components/ui/Spinner.jsx";
import { useCheckout } from "../../hooks/useCheckout";

export default function ShippingPage() {
  const navigate = useNavigate();
  const { basket, shipping, loading, saving, error, saveAddress, selectMethod } = useCheckout();
  const lines = basket?.lines || [];

  async function handleAddressSubmit(address) {
    await saveAddress(address);
  }

  async function handleMethodSelect(methodCode) {
    await selectMethod(methodCode);
  }

  if (loading) return <Spinner label="Loading checkout" />;
  if (!loading && basket?.is_empty) return <Navigate to="/checkout/cart" replace />;

  const selectedCode = shipping?.selected_method?.code || "";
  const canContinue = Boolean(shipping?.ready_for_checkout);

  return (
    <section className="checkout-page">
      <CheckoutStepper current="shipping" />

      <div className="checkout-title-row">
        <Link className="back-link" to="/checkout/cart">
          <MaterialIcon name="arrow_back" size={18} /> Cart
        </Link>
        <h1>Delivery</h1>
      </div>

      <Alert>{error}</Alert>

      <div className="checkout-layout">
        <div className="checkout-stack">
          <ShippingAddressForm
            address={shipping?.address}
            countries={shipping?.countries || []}
            saving={saving}
            onSubmit={handleAddressSubmit}
          />
          <ShippingMethodSelector
            methods={shipping?.methods || []}
            selectedCode={selectedCode}
            saving={saving}
            onSelect={handleMethodSelect}
          />
          <button className="primary-button checkout-submit" type="button" disabled={!canContinue || saving} onClick={() => navigate("/checkout/payment")}>
            <MaterialIcon name="arrow_forward" size={19} />
            Continue to payment
          </button>
        </div>
        <OrderSummaryPanel basket={basket} shipping={shipping} loading={saving} />
      </div>

      {!lines.length ? <Alert>Your cart is empty.</Alert> : null}
    </section>
  );
}
