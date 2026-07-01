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
  const [selectedAddressId, setSelectedAddressId] = useState("");
  const lines = basket?.lines || [];

  useEffect(() => {
    if (user) void loadAddresses().catch(() => {});
  }, [loadAddresses, user]);

  const hasSavedAddresses = Boolean(user && addresses.length);
  const selectedAddress = addresses.find((address) => String(address.id) === String(selectedAddressId)) || null;
  const fallbackAddress = hasSavedAddresses ? addresses.find((address) => address.is_default_for_shipping) || addresses[0] : null;
  const showSavedAddressPicker = hasSavedAddresses && deliveryMode !== "new";
  const showDeliveryForm = !hasSavedAddresses || deliveryMode === "new";

  useEffect(() => {
    if (!hasSavedAddresses) {
      setSelectedAddressId("");
      return;
    }
    if (!selectedAddressId || !addresses.some((address) => String(address.id) === String(selectedAddressId))) {
      setSelectedAddressId(String(fallbackAddress?.id || ""));
    }
  }, [addresses, fallbackAddress?.id, hasSavedAddresses, selectedAddressId]);

  async function handleAddressSubmit(address) {
    try {
      await saveAddress(address);
      await saveBillingAddress({ ...address, phone_number: address.phone_number || "" });
      const latestAddresses = await loadAddresses();
      const newestAddress = findMatchingSavedAddress(address, latestAddresses) || latestAddresses[0];
      if (newestAddress?.id) setSelectedAddressId(String(newestAddress.id));
      setDeliveryMode("saved");
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
      setSelectedAddressId(String(address.id));
      setDeliveryMode("saved");
    } catch {
      // Hook state already exposes the normalized message.
    }
  }

  function handleSavedAddressChange(event) {
    const addressId = event.target.value;
    setSelectedAddressId(addressId);
    const address = addresses.find((item) => String(item.id) === String(addressId));
    if (address) void handleUseShippingAddress(address);
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
  const editingDeliveryDetails = showDeliveryForm;
  const canContinue = Boolean(shipping?.ready_for_checkout && !editingDeliveryDetails);
  const summaryShipping = editingDeliveryDetails ? null : shipping;

  return (
    <section className="checkout-page">
      <CheckoutStepper current="shipping" basket={basket} shipping={shipping} />

      <Alert>{error}</Alert>

      <div className="checkout-layout">
        <div className="checkout-stack">
          {showSavedAddressPicker ? (
            <section className="checkout-card delivery-choice-card">
              <div className="checkout-card__title">
                <span><MaterialIcon name="contacts" size={20} /></span>
                <div>
                  <h2>Delivery details</h2>
                </div>
              </div>
              <label className="saved-address-select">
                <span>Choose saved delivery</span>
                <select value={selectedAddressId} disabled={saving} onChange={handleSavedAddressChange}>
                  {addresses.map((address) => (
                    <option value={address.id} key={address.id}>
                      {addressOptionLabel(address)}
                    </option>
                  ))}
                </select>
              </label>
              {selectedAddress ? (
                <div className="previous-address-summary">
                  <div>
                    <strong>{addressTitle(selectedAddress)}</strong>
                    <span>{addressLines(selectedAddress)}</span>
                    {selectedAddress.phone_number ? <small>{selectedAddress.phone_number}</small> : null}
                  </div>
                  {shipping?.address && deliveryMode !== "new" ? <em>Selected</em> : null}
                </div>
              ) : null}
              <div className="delivery-choice-actions">
                <button className="primary-button" type="button" disabled={saving || !selectedAddress} onClick={() => handleUseShippingAddress(selectedAddress)}>
                  <MaterialIcon name="task_alt" size={18} />
                  Use selected delivery
                </button>
                <button className="secondary-button" type="button" disabled={saving} onClick={handleCreateNewDetails}>
                  <MaterialIcon name="add_location_alt" size={18} />
                  Create new delivery
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
          {editingDeliveryDetails ? (
            <section className="checkout-card checkout-note-panel delivery-save-required">
              <MaterialIcon name="info" size={20} />
              <div>
                <strong>Save delivery details to calculate delivery.</strong>
                <span>The price below will update after the pinned location is saved.</span>
              </div>
            </section>
          ) : (
            <ShippingMethodSelector
              methods={shipping?.methods || []}
              selectedCode={selectedCode}
              saving={saving}
              onSelect={handleMethodSelect}
            />
          )}
          <button className="primary-button checkout-submit" type="button" disabled={!canContinue || saving} onClick={() => navigate("/checkout/payment")}>
            <MaterialIcon name="arrow_forward" size={19} />
            Continue to payment
          </button>
        </div>
        <OrderSummaryPanel basket={basket} shipping={summaryShipping} loading={saving} />
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

function addressOptionLabel(address) {
  const title = addressTitle(address);
  const city = [address.line4, address.state].filter(Boolean).join(", ");
  return city ? `${title} - ${city}` : title;
}

function hasAddressContent(address) {
  if (!address) return false;
  return ["first_name", "last_name", "line1", "line2", "line3", "line4", "state", "postcode", "country_code", "phone_number"]
    .some((key) => Boolean(address[key]));
}

function findMatchingSavedAddress(address, savedAddresses) {
  const normalized = normalizeAddressParts(address);
  return savedAddresses.find((savedAddress) => {
    const candidate = normalizeAddressParts(savedAddress);
    return ["line1", "line2", "line3", "line4", "postcode", "country_code", "phone_number"].every(
      (key) => candidate[key] === normalized[key]
    );
  });
}

function normalizeAddressParts(address) {
  return {
    line1: normalizePart(address?.line1),
    line2: normalizePart(address?.line2),
    line3: normalizePart(address?.line3),
    line4: normalizePart(address?.line4),
    postcode: normalizePart(address?.postcode),
    country_code: normalizePart(address?.country_code || address?.country?.iso_3166_1_a2),
    phone_number: normalizePart(address?.phone_number)
  };
}

function normalizePart(value) {
  return String(value || "").trim().toLowerCase();
}
