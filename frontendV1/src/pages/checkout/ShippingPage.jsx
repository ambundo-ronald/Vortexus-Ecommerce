import { useEffect, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import Swal from "sweetalert2";

import { quotesApi } from "../../api/quotes.api";
import CheckoutStepper from "../../components/checkout/CheckoutStepper.jsx";
import OrderSummaryPanel from "../../components/checkout/OrderSummaryPanel.jsx";
import ShippingAddressForm from "../../components/checkout/ShippingAddressForm.jsx";
import ShippingMethodSelector from "../../components/checkout/ShippingMethodSelector.jsx";
import Alert from "../../components/ui/Alert.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import Spinner from "../../components/ui/Spinner.jsx";
import { useAuth } from "../../hooks/useAuth";
import { useCheckout } from "../../hooks/useCheckout";
import { useUiStore } from "../../store/ui.store";
import { formatCurrency } from "../../utils/currency";
import "./CheckoutFlow.css";

const MPESA_TRANSACTION_LIMIT_KES = 150000;
const LOGISTICS_DELIVERY_LIMIT_KES = 1500;
const LOGISTICS_PHONE = "+0141316578";
const LOGISTICS_EMAIL = "logistics@reesolmart.com";

export default function ShippingPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const notify = useUiStore((state) => state.notify);
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
  const [quotePromptOpen, setQuotePromptOpen] = useState(false);
  const [quoteSubmitting, setQuoteSubmitting] = useState(false);
  const [quoteSuccess, setQuoteSuccess] = useState("");
  const [quoteError, setQuoteError] = useState("");
  const [logisticsAlertKey, setLogisticsAlertKey] = useState("");
  const lines = basket?.lines || [];
  const hasSavedAddresses = Boolean(user && addresses.length);
  const selectedAddress = addresses.find((address) => String(address.id) === String(selectedAddressId)) || null;
  const fallbackAddress = hasSavedAddresses ? addresses.find((address) => address.is_default_for_shipping) || addresses[0] : null;
  const showSavedAddressPicker = hasSavedAddresses && deliveryMode !== "new";
  const showDeliveryForm = !hasSavedAddresses || deliveryMode === "new";
  const selectedCode = shipping?.selected_method?.code || "";
  const editingDeliveryDetails = showDeliveryForm;
  const shippingMethods = shipping?.methods || [];
  const dispatchHubPickup = shippingMethods.find((method) => isDispatchHubPickup(method));
  const deliveryFeeAboveLimit = shippingMethods.some((method) => !isDispatchHubPickup(method) && Number(method.charge || 0) > LOGISTICS_DELIVERY_LIMIT_KES);
  const visibleShippingMethods = deliveryFeeAboveLimit && dispatchHubPickup ? [dispatchHubPickup] : shippingMethods;
  const canContinue = Boolean(shipping?.ready_for_checkout && !editingDeliveryDetails && hasPinnedAddress(shipping?.address));
  const summaryShipping = editingDeliveryDetails ? null : shipping;
  const baseOrderTotal = Number(shipping?.totals?.base_order_total ?? basket?.totals?.base_subtotal ?? 0);
  const exceedsMpesaLimit = baseOrderTotal > MPESA_TRANSACTION_LIMIT_KES;

  useEffect(() => {
    if (user) void loadAddresses().catch(() => {});
  }, [loadAddresses, user]);

  useEffect(() => {
    if (!hasSavedAddresses) {
      setSelectedAddressId("");
      return;
    }
    if (!selectedAddressId || !addresses.some((address) => String(address.id) === String(selectedAddressId))) {
      setSelectedAddressId(String(fallbackAddress?.id || ""));
    }
  }, [addresses, fallbackAddress?.id, hasSavedAddresses, selectedAddressId]);

  useEffect(() => {
    if (!deliveryFeeAboveLimit || !dispatchHubPickup) return;

    const alertKey = `${shipping?.address?.id || "address"}:${dispatchHubPickup.code}`;
    if (logisticsAlertKey !== alertKey) {
      setLogisticsAlertKey(alertKey);
      void showLogisticsLimitAlert();
    }

    if (dispatchHubPickup.code && selectedCode !== dispatchHubPickup.code) {
      void selectMethod(dispatchHubPickup.code).catch(() => {});
    }
  }, [deliveryFeeAboveLimit, dispatchHubPickup, logisticsAlertKey, selectMethod, selectedCode, shipping?.address?.id]);

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

    if (!hasPinnedAddress(address)) {
      await Swal.fire({
        icon: "warning",
        title: "Pin delivery location",
        text: "This saved delivery does not have a pinned location. Please create a new delivery point and pin the location before continuing.",
        confirmButtonText: "Create new delivery",
        confirmButtonColor: "#2563eb"
      });
      setDeliveryMode("new");
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

  function handleContinueToPayment() {
    if (exceedsMpesaLimit) {
      setQuotePromptOpen(true);
      return;
    }
    navigate("/checkout/payment");
  }

  async function submitHighValueQuote() {
    setQuoteSubmitting(true);
    setQuoteError("");
    setQuoteSuccess("");
    try {
      const response = await quotesApi.create({
        name: [user?.first_name, user?.last_name].filter(Boolean).join(" ") || user?.full_name || user?.email || "Customer",
        email: user?.email || "",
        phone: shipping?.address?.phone_number || selectedAddress?.phone_number || "",
        company: shipping?.address?.line3 || selectedAddress?.line3 || "",
        message: buildHighValueQuoteMessage({ basket, shipping, total: baseOrderTotal })
      });
      const message = response.detail || "Quote request received. Our team will contact you shortly.";
      setQuoteSuccess(message);
      notify({ title: "Quote request sent", message, icon: "request_quote" });
    } catch (requestError) {
      const message = requestError.normalized?.message || requestError.message || "Could not submit quote request.";
      setQuoteError(message);
      notify({ tone: "danger", title: "Quote request failed", message, icon: "request_quote" });
    } finally {
      setQuoteSubmitting(false);
    }
  }

  if (loading) return <Spinner label="Loading checkout" />;
  if (!loading && basket?.is_empty) return <Navigate to="/checkout/cart" replace />;
  return (
    <section className="checkout-page">
      <CheckoutStepper
        current="shipping"
        basket={basket}
        shipping={shipping}
        paymentBlocked={exceedsMpesaLimit}
        onPaymentBlocked={() => setQuotePromptOpen(true)}
      />

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
              autoSubmitOnLocationChange
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
              methods={visibleShippingMethods}
              selectedCode={selectedCode}
              saving={saving}
              onSelect={handleMethodSelect}
            />
          )}
          <button className="primary-button checkout-submit" type="button" disabled={!canContinue || saving} onClick={handleContinueToPayment}>
            <MaterialIcon name="arrow_forward" size={19} />
            Continue to payment
          </button>
        </div>
        <OrderSummaryPanel basket={basket} shipping={summaryShipping} loading={saving} />
      </div>

      {!lines.length ? <Alert>Your cart is empty.</Alert> : null}
      {quotePromptOpen ? (
        <HighValueQuoteModal
          total={baseOrderTotal}
          submitting={quoteSubmitting}
          success={quoteSuccess}
          error={quoteError}
          onClose={() => setQuotePromptOpen(false)}
          onSubmit={submitHighValueQuote}
        />
      ) : null}
    </section>
  );
}

function HighValueQuoteModal({ total, submitting, success, error, onClose, onSubmit }) {
  return (
    <div className="quote-limit-modal" role="dialog" aria-modal="true" aria-labelledby="quote-limit-title">
      <div className="quote-limit-modal__panel">
        <button className="quote-limit-modal__close" type="button" onClick={onClose} aria-label="Close">
          <MaterialIcon name="close" size={18} />
        </button>
        <div className="quote-limit-modal__icon">
          <MaterialIcon name="request_quote" size={28} />
        </div>
        <h2 id="quote-limit-title">Request quotation</h2>
        <p>
          Your order total is {formatCurrency(total, "KES")}. M-Pesa allows up to{" "}
          {formatCurrency(MPESA_TRANSACTION_LIMIT_KES, "KES")} per transaction, so this order needs a quotation before payment.
        </p>
        <Alert tone="success">{success}</Alert>
        <Alert>{error}</Alert>
        <div className="quote-limit-modal__actions">
          {success ? (
            <button className="primary-button" type="button" onClick={onClose}>
              <MaterialIcon name="check_circle" size={19} />
              Done
            </button>
          ) : (
            <button className="primary-button" type="button" disabled={submitting} onClick={onSubmit}>
              <MaterialIcon name="request_quote" size={19} />
              {submitting ? "Sending..." : "Request quotation"}
            </button>
          )}
          {!success ? (
            <button className="secondary-button" type="button" disabled={submitting} onClick={onClose}>
              Cancel
            </button>
          ) : null}
        </div>
      </div>
    </div>
  );
}

function buildHighValueQuoteMessage({ basket, shipping, total }) {
  const lines = basket?.lines || [];
  const items = lines
    .map((line) => {
      const title = line.product?.title || line.title || "Product";
      return `${line.quantity}x ${title}`;
    })
    .join("; ");
  const delivery = shipping?.address
    ? [shipping.address.line1, shipping.address.line2, shipping.address.line3, shipping.address.line4, shipping.address.state]
        .filter(Boolean)
        .join(", ")
    : "Delivery address not provided";
  return [
    "Please prepare a quotation for this high-value checkout.",
    `Cart total: ${formatCurrency(total, "KES")}.`,
    `Reason: M-Pesa transaction limit is ${formatCurrency(MPESA_TRANSACTION_LIMIT_KES, "KES")}.`,
    items ? `Items: ${items}.` : "",
    `Delivery: ${delivery}.`
  ].filter(Boolean).join("\n");
}

function isDispatchHubPickup(method) {
  const name = String(method?.name || "").toLowerCase();
  const code = String(method?.code || "").toLowerCase();
  return Boolean(method?.is_pickup || name.includes("dispatch hub pickup") || code.includes("dispatch") || code.includes("pickup"));
}

function hasPinnedAddress(address) {
  if (!address) return false;
  const latitude = address.location?.latitude ?? address.latitude;
  const longitude = address.location?.longitude ?? address.longitude;
  return latitude !== null && latitude !== undefined && latitude !== "" && longitude !== null && longitude !== undefined && longitude !== "";
}

function showLogisticsLimitAlert() {
  return Swal.fire({
    icon: "info",
    title: "Contact logistics team",
    html: `
      <p style="margin: 0 0 12px;">This delivery requires logistics support. Please email or call our logistics team before continuing with delivery.</p>
      <p style="margin: 0;"><strong>Phone:</strong> <a href="tel:${LOGISTICS_PHONE}">${LOGISTICS_PHONE}</a></p>
      <p style="margin: 6px 0 0;"><strong>Email:</strong> <a href="mailto:${LOGISTICS_EMAIL}">${LOGISTICS_EMAIL}</a></p>
    `,
    confirmButtonText: "OK",
    confirmButtonColor: "#2563eb"
  });
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
