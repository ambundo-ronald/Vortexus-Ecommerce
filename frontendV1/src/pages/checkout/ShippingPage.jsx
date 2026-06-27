import { useEffect, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";

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
  const [deliveryMode, setDeliveryMode] = useState("saved");
  const lines = basket?.lines || [];

  useEffect(() => {
    if (user) void loadAddresses().catch(() => {});
  }, [loadAddresses, user]);

  const hasSavedAddresses = Boolean(user && addresses.length);
  const previousAddress = hasSavedAddresses
    ? addresses.find((address) => address.is_default_for_shipping) || addresses[0]
    : hasAddressContent(shipping?.address) ? shipping.address : null;
  const showPreviousChoice = Boolean(previousAddress && deliveryMode !== "new");
  const showDeliveryForm = !previousAddress || deliveryMode === "new";

  async function handleAddressSubmit(address) {
    try {
      await saveAddress(address);
      await saveBillingAddress({ ...address, phone_number: address.phone_number || "" });
    } catch {
      // Hook state already exposes the normalized message.
    }
  }

  async function handleUseShippingAddress(address) {
    if (!address?.id) {
      setDeliveryMode("saved");
      return;
    }

    try {
      await useShippingAddress(address.id);
      await useBillingAddress(address.id);
      setDeliveryMode("saved");
    } catch {
      // Hook state already exposes the normalized message.
    }
  }

  function handleCreateNewDetails() {
    setDeliveryMode("new");
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
      <CheckoutStepper current="shipping" basket={basket} shipping={shipping} />

      <Alert>{error}</Alert>

      <div className="checkout-layout">
        <div className="checkout-stack">
          {showPreviousChoice ? (
            <section className="checkout-card delivery-choice-card">
              <div className="checkout-card__title">
                <span><MaterialIcon name="contacts" size={20} /></span>
                <div>
                  <h2>Delivery details</h2>
                </div>
              </div>
              <div className="previous-address-summary">
                <div>
                  <strong>{addressTitle(previousAddress)}</strong>
                  <span>{addressLines(previousAddress)}</span>
                  {previousAddress.phone_number ? <small>{previousAddress.phone_number}</small> : null}
                </div>
                {shipping?.address && deliveryMode !== "new" ? <em>Selected</em> : null}
              </div>
              <div className="delivery-choice-actions">
                <button className="primary-button" type="button" disabled={saving} onClick={() => handleUseShippingAddress(previousAddress)}>
                  <MaterialIcon name="task_alt" size={18} />
                  Use previous details
                </button>
                <button className="secondary-button" type="button" disabled={saving} onClick={handleCreateNewDetails}>
                  <MaterialIcon name="add_location_alt" size={18} />
                  Create new details
                </button>
              </div>
            </section>
          ) : null}
          {showDeliveryForm ? (
            <ShippingAddressForm
              address={deliveryMode === "new" ? null : shipping?.address}
              countries={shipping?.countries || []}
              saving={saving}
              onSubmit={handleAddressSubmit}
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

function addressTitle(address) {
  return address.title || [address.first_name, address.last_name].filter(Boolean).join(" ") || "Previous delivery address";
}

function addressLines(address) {
  return [address.line1, address.line2, address.line3, address.line4, address.state, address.postcode, address.country_code]
    .filter(Boolean)
    .join(", ") || "Saved delivery details";
}

function hasAddressContent(address) {
  if (!address) return false;
  return ["first_name", "last_name", "line1", "line2", "line3", "line4", "state", "postcode", "country_code", "phone_number"]
    .some((key) => Boolean(address[key]));
}
