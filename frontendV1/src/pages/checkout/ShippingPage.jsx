import { useEffect, useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";

import AddressCard from "../../components/account/AddressCard.jsx";
import CheckoutStepper from "../../components/checkout/CheckoutStepper.jsx";
import OrderSummaryPanel from "../../components/checkout/OrderSummaryPanel.jsx";
import ShippingAddressForm from "../../components/checkout/ShippingAddressForm.jsx";
import ShippingMethodSelector from "../../components/checkout/ShippingMethodSelector.jsx";
import Alert from "../../components/ui/Alert.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import Spinner from "../../components/ui/Spinner.jsx";
import { useAuth } from "../../hooks/useAuth";
import { useCheckout } from "../../hooks/useCheckout";
import "./CheckoutFlow.css";

export default function ShippingPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const {
    basket,
    shipping,
    billing,
    addresses,
    loading,
    saving,
    error,
    loadAddresses,
    saveAddress,
    useShippingAddress,
    saveBillingAddress,
    useBillingAddress,
    selectMethod
  } = useCheckout();
  const [sameAsDelivery, setSameAsDelivery] = useState(true);
  const lines = basket?.lines || [];

  useEffect(() => {
    if (user) void loadAddresses().catch(() => {});
  }, [loadAddresses, user]);

  async function handleAddressSubmit(address) {
    try {
      await saveAddress(address);
      if (sameAsDelivery) await saveBillingAddress({ ...address, phone_number: address.phone_number || "" });
    } catch {
      // Hook state already exposes the normalized message.
    }
  }

  async function handleBillingSubmit(address) {
    try {
      await saveBillingAddress(address);
      setSameAsDelivery(false);
    } catch {
      // Hook state already exposes the normalized message.
    }
  }

  async function handleUseShippingAddress(address) {
    try {
      await useShippingAddress(address.id);
      if (sameAsDelivery) await useBillingAddress(address.id);
    } catch {
      // Hook state already exposes the normalized message.
    }
  }

  async function handleUseBillingAddress(address) {
    try {
      await useBillingAddress(address.id);
      setSameAsDelivery(false);
    } catch {
      // Hook state already exposes the normalized message.
    }
  }

  async function handleMethodSelect(methodCode) {
    try {
      await selectMethod(methodCode);
    } catch {
      // Hook state already exposes the normalized message.
    }
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
          {user && addresses.length ? (
            <section className="checkout-card saved-address-picker">
              <div className="checkout-card__title">
                <span><MaterialIcon name="contacts" size={20} /></span>
                <div>
                  <h2>Saved addresses</h2>
                  <p>Use a saved address for delivery or billing.</p>
                </div>
              </div>
              <div className="address-grid address-grid--compact">
                {addresses.map((address) => (
                  <AddressCard
                    key={address.id}
                    address={address}
                    loading={saving}
                    onUse={handleUseShippingAddress}
                    onDefaultBilling={handleUseBillingAddress}
                  />
                ))}
              </div>
            </section>
          ) : null}
          <ShippingAddressForm
            address={shipping?.address}
            countries={shipping?.countries || []}
            saving={saving}
            onSubmit={handleAddressSubmit}
          />
          <section className="checkout-card billing-toggle-card">
            <label className="auth-check">
              <input
                type="checkbox"
                checked={sameAsDelivery}
                onChange={(event) => setSameAsDelivery(event.target.checked)}
              />
              <span>Use delivery address for billing</span>
            </label>
            {billing?.address ? (
              <p className="checkout-note">
                Billing address: {[billing.address.line1, billing.address.line4, billing.address.country_code].filter(Boolean).join(", ")}
              </p>
            ) : null}
          </section>
          {!sameAsDelivery ? (
            <ShippingAddressForm
              address={billing?.address}
              countries={shipping?.countries || []}
              saving={saving}
              title="Billing details"
              description="Use this for invoices and payment records."
              icon="receipt_long"
              submitLabel="Save billing details"
              requirePhone={false}
              onSubmit={handleBillingSubmit}
            />
          ) : null}
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
