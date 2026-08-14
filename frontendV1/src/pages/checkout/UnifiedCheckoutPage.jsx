import { useEffect, useRef, useState } from "react";
import { Navigate, useNavigate, useSearchParams } from "react-router-dom";
import Swal from "sweetalert2";

import CheckoutStepper from "../../components/checkout/CheckoutStepper.jsx";
import OrderSummaryPanel from "../../components/checkout/OrderSummaryPanel.jsx";
import PaymentMethodSelector from "../../components/checkout/PaymentMethodSelector.jsx";
import ShippingAddressForm from "../../components/checkout/ShippingAddressForm.jsx";
import ShippingMethodSelector from "../../components/checkout/ShippingMethodSelector.jsx";
import PaymentProgressPanel from "../../components/payment/PaymentProgressPanel.jsx";
import Alert from "../../components/ui/Alert.jsx";
import MaterialIcon from "../../components/ui/MaterialIcon.jsx";
import Spinner from "../../components/ui/Spinner.jsx";
import { useAuth } from "../../hooks/useAuth";
import { useCheckout } from "../../hooks/useCheckout";
import { usePayment } from "../../hooks/usePayment";
import { useUiStore } from "../../store/ui.store";
import { trackStorefrontEvent } from "../../utils/analytics";
import { formatCurrency } from "../../utils/currency";
import {
  PAYMENT_CONFIRMATION_TIMEOUT_MS,
  PAYMENT_CONFIRMATION_TIMEOUT_MESSAGE,
  isPaymentComplete,
  isPaymentFailed,
  paymentRequiresPrepayment,
  readPendingCheckout,
  storePendingCheckout
} from "../../utils/payment";
import "./CheckoutFlow.css";

const MPESA_TRANSACTION_LIMIT_KES = 150000;
const HIGH_VALUE_DEPOSIT_METHOD = "high_value_deposit";
const KCB_PAYBILL_BUSINESS_NUMBER = "522522";
const KCB_PAYBILL_ACCOUNT_NUMBER = "1354483790";
const LOGISTICS_DELIVERY_LIMIT_KES = 1500;
const LOGISTICS_PHONE = "+0141316578";
const LOGISTICS_EMAIL = "logistics@reesolmart.com";

export default function UnifiedCheckoutPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { user } = useAuth();
  const notify = useUiStore((state) => state.notify);
  const checkoutState = useCheckout();
  const paymentState = usePayment();
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
    selectMethod,
    previewCheckout,
    placeOrder
  } = checkoutState;

  const [deliveryMode, setDeliveryMode] = useState("saved");
  const [selectedAddressId, setSelectedAddressId] = useState("");
  const [quotePromptOpen, setQuotePromptOpen] = useState(false);
  const [quoteSubmitting, setQuoteSubmitting] = useState(false);
  const [quoteSuccess, setQuoteSuccess] = useState("");
  const [quoteError, setQuoteError] = useState("");
  const [depositCode, setDepositCode] = useState("");
  const [logisticsAlertKey, setLogisticsAlertKey] = useState("");
  const [activePayment, setActivePayment] = useState(null);
  const [activeMethod, setActiveMethod] = useState(null);
  const [guestEmail, setGuestEmail] = useState("");
  const [lastPaymentForm, setLastPaymentForm] = useState(null);
  const [checkingStatus, setCheckingStatus] = useState(false);
  const [confirmationStartedAt, setConfirmationStartedAt] = useState(null);
  const [clockTick, setClockTick] = useState(() => Date.now());
  const checkoutStartedRef = useRef(false);
  const defaultAddressAutoUsedRef = useRef("");
  const pendingReturnHandledRef = useRef("");
  const timeoutTrackedRef = useRef("");

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
  const estimatedShippingMethods = shipping?.estimated_methods || [];
  const shippingReady = Boolean(shipping?.ready_for_checkout && !editingDeliveryDetails && hasPinnedAddress(shipping?.address));
  const baseOrderTotal = Number(shipping?.totals?.base_order_total ?? basket?.totals?.base_subtotal ?? 0);
  const exceedsMpesaLimit = baseOrderTotal > MPESA_TRANSACTION_LIMIT_KES;
  const paymentError = paymentState.error;
  const visiblePaymentError = paymentError === PAYMENT_CONFIRMATION_TIMEOUT_MESSAGE ? "" : paymentError;
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
    user?.payment_permissions?.cash_on_delivery_available ? "cod-available" : "cod-unavailable",
    user?.bank_transfer_allowed ? "bank-allowed" : "bank-default",
    user?.payment_permissions?.bank_transfer_available ? "bank-available" : "bank-unavailable"
  ].join(":");

  function checkoutMetadata(extra = {}) {
    return {
      item_count: basket?.item_count || lines.length,
      line_count: lines.length,
      currency: shipping?.totals?.currency || basket?.currency || "",
      subtotal: shipping?.totals?.subtotal ?? basket?.totals?.subtotal,
      shipping_total: shipping?.totals?.shipping_total,
      order_total: shipping?.totals?.order_total ?? basket?.totals?.order_total,
      has_saved_addresses: hasSavedAddresses,
      shipping_method: selectedCode,
      payment_method: activePayment?.method || activeMethod?.code || lastPaymentForm?.method || "",
      payment_status: activePayment?.status || "",
      payment_reference: activePayment?.reference || "",
      provider_reference: activePayment?.provider_reference || "",
      quote_required: exceedsMpesaLimit,
      remaining_seconds: remainingSeconds,
      ...extra
    };
  }

  useEffect(() => {
    if (user) void loadAddresses().catch(() => {});
  }, [loadAddresses, user]);

  useEffect(() => {
    void paymentState.loadMethods();
  }, [paymentState.loadMethods, userPaymentStateKey]);

  useEffect(() => {
    if (loading || checkoutStartedRef.current) return;
    checkoutStartedRef.current = true;
    trackStorefrontEvent("shipping_started", checkoutMetadata({ source: "unified_checkout" }));
    trackStorefrontEvent("payment_started", checkoutMetadata({ source: "unified_checkout" }));
  }, [loading]);

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
    if (!hasSavedAddresses || deliveryMode === "new" || saving) return;
    const defaultAddress = addresses.find((address) => address.is_default_for_shipping && hasPinnedAddress(address));
    if (!defaultAddress?.id) return;
    if (shipping?.address?.id && String(shipping.address.id) === String(defaultAddress.id)) return;
    const autoKey = `${defaultAddress.id}:${defaultAddress.location?.latitude ?? defaultAddress.latitude}:${defaultAddress.location?.longitude ?? defaultAddress.longitude}`;
    if (defaultAddressAutoUsedRef.current === autoKey) return;
    defaultAddressAutoUsedRef.current = autoKey;
    setSelectedAddressId(String(defaultAddress.id));
    void handleUseShippingAddress(defaultAddress, { auto: true });
  }, [addresses, deliveryMode, hasSavedAddresses, saving, shipping?.address?.id]);

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

  useEffect(() => {
    if (!activePayment || !confirmationStartedAt || isPaymentComplete(activePayment) || isPaymentFailed(activePayment)) return undefined;
    const timer = window.setInterval(() => setClockTick(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, [activePayment, confirmationStartedAt]);

  useEffect(() => {
    if (!paymentTimedOut || !activePayment?.reference || timeoutTrackedRef.current === activePayment.reference) return;
    timeoutTrackedRef.current = activePayment.reference;
    trackStorefrontEvent("payment_timeout", checkoutMetadata({
      payment_method: activePayment.method,
      payment_status: activePayment.status,
      payment_reference: activePayment.reference
    }));
  }, [activePayment, paymentTimedOut]);

  useEffect(() => {
    const pending = readPendingCheckout(searchParams);
    if (!pending?.payment_reference || pendingReturnHandledRef.current === pending.payment_reference) return;
    pendingReturnHandledRef.current = pending.payment_reference;
    setActivePayment(pending.payment);
    setActiveMethod(pending.method || null);
    setGuestEmail(pending.guest_email || "");
    void confirmPaymentAndCreateOrder(pending.payment, pending.method || null, pending.guest_email || "");
  }, [searchParams]);

  async function handleAddressSubmit(address) {
    trackStorefrontEvent("shipping_save_attempted", checkoutMetadata({
      country_code: address?.country_code,
      has_coordinates: hasPinnedAddress(address)
    }));
    try {
      await saveAddress(address);
      await saveBillingAddress({ ...address, phone_number: address.phone_number || "" });
      const latestAddresses = await loadAddresses();
      const newestAddress = findMatchingSavedAddress(address, latestAddresses) || latestAddresses[0];
      if (newestAddress?.id) setSelectedAddressId(String(newestAddress.id));
      setDeliveryMode("saved");
      trackStorefrontEvent("shipping_saved", checkoutMetadata({
        selected_address_id: newestAddress?.id,
        country_code: address?.country_code,
        has_coordinates: hasPinnedAddress(address)
      }));
    } catch {
      trackStorefrontEvent("shipping_save_failed", checkoutMetadata({
        country_code: address?.country_code,
        has_coordinates: hasPinnedAddress(address)
      }));
    }
  }

  async function handleUseShippingAddress(address, options = {}) {
    if (!address?.id) {
      setDeliveryMode("saved");
      return;
    }

    trackStorefrontEvent("saved_shipping_selected", checkoutMetadata({
      selected_address_id: address.id,
      has_coordinates: hasPinnedAddress(address),
      source: options.auto ? "default_address_auto" : "saved_address_picker"
    }));

    if (!hasPinnedAddress(address)) {
      trackStorefrontEvent("saved_shipping_missing_pin", checkoutMetadata({
        selected_address_id: address.id,
        has_coordinates: false
      }));
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
      trackStorefrontEvent("saved_shipping_used", checkoutMetadata({
        selected_address_id: address.id,
        has_coordinates: true,
        source: options.auto ? "default_address_auto" : "saved_address_picker"
      }));
    } catch {
      trackStorefrontEvent("saved_shipping_failed", checkoutMetadata({
        selected_address_id: address.id,
        has_coordinates: hasPinnedAddress(address)
      }));
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
    trackStorefrontEvent("shipping_new_address_started", checkoutMetadata());
  }

  async function handleMethodSelect(methodCode) {
    const method = shippingMethods.find((item) => item.code === methodCode);
    try {
      await selectMethod(methodCode);
      trackStorefrontEvent("shipping_method_selected", checkoutMetadata({
        shipping_method: methodCode,
        shipping_method_name: method?.name || ""
      }));
    } catch {
      trackStorefrontEvent("shipping_method_failed", checkoutMetadata({
        shipping_method: methodCode,
        shipping_method_name: method?.name || ""
      }));
    }
  }

  async function handlePaymentSubmit(form) {
    setLastPaymentForm(form);
    setConfirmationStartedAt(null);
    setClockTick(Date.now());
    trackStorefrontEvent("payment_method_selected", checkoutMetadata({
      payment_method: form?.method || "",
      source: "unified_checkout"
    }));

    try {
      const preview = await previewCheckout();
      if (preview && !preview.ready) {
        const missing = preview.missing || [];
        trackStorefrontEvent("payment_blocked_checkout_incomplete", checkoutMetadata({
          payment_method: form?.method || "",
          missing: missing.join(",")
        }));
        notify({
          tone: "warning",
          title: "Checkout needs one more step",
          message: missing.includes("shipping_address") ? "Add a delivery address before paying." : "Select a delivery method before paying.",
          icon: "info"
        });
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

      const pendingPayload = {
        payment_reference: payment.reference,
        payment,
        method: selectedMethod || null,
        guest_email: form.payerEmail
      };
      storePendingCheckout(pendingPayload);

      if (payment.method === "pesapal" && payment.redirect_url) {
        trackStorefrontEvent("payment_redirect_started", checkoutMetadata({
          payment_method: payment.method,
          payment_status: payment.status,
          payment_reference: payment.reference
        }));
        window.location.assign(payment.redirect_url);
        return;
      }

      const requiresPrepayment = paymentRequiresPrepayment(selectedMethod);
      trackStorefrontEvent(requiresPrepayment ? "payment_prompt_sent" : "payment_initialized", checkoutMetadata({
        payment_method: payment.method,
        payment_status: payment.status,
        payment_reference: payment.reference,
        provider_reference: payment.provider_reference,
        requires_prepayment: requiresPrepayment
      }));

      if (!requiresPrepayment || isPaymentComplete(payment)) {
        await createOrderFromPayment(payment, selectedMethod, form.payerEmail);
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
          storePendingCheckout({ ...pendingPayload, payment: nextPayment });
        }
      });
      setActivePayment(finalPayment);
      await createOrderFromPayment(finalPayment, selectedMethod, form.payerEmail);
    } catch {
      trackStorefrontEvent("payment_prompt_failed", checkoutMetadata({
        payment_method: form?.method || "",
        reason: "initialize_confirm_or_order_failed"
      }));
    }
  }

  async function confirmPaymentAndCreateOrder(payment, method, payerEmail) {
    if (!payment?.reference) return;
    setCheckingStatus(true);
    const startedAt = Date.now();
    setConfirmationStartedAt(startedAt);
    setClockTick(startedAt);
    try {
      const finalPayment = await paymentState.waitForPayment(payment, {
        timeoutMs: PAYMENT_CONFIRMATION_TIMEOUT_MS,
        onUpdate: (nextPayment) => {
          if (!nextPayment) return;
          setActivePayment(nextPayment);
          storePendingCheckout({
            payment_reference: nextPayment.reference,
            payment: nextPayment,
            method,
            guest_email: payerEmail
          });
        }
      });
      setActivePayment(finalPayment);
      await createOrderFromPayment(finalPayment, method, payerEmail);
    } catch {
      // Hook state already exposes the normalized message.
    } finally {
      setCheckingStatus(false);
    }
  }

  async function createOrderFromPayment(payment, method, payerEmail) {
    if (paymentRequiresPrepayment(method || payment?.method) && !isPaymentComplete(payment)) {
      trackStorefrontEvent("order_place_blocked", checkoutMetadata({
        reason: isPaymentFailed(payment) ? "payment_failed" : "payment_pending",
        payment_method: payment?.method || method?.code || "",
        payment_status: payment?.status || "",
        payment_reference: payment?.reference || ""
      }));
      return;
    }

    trackStorefrontEvent("order_place_clicked", checkoutMetadata({
      payment_method: payment?.method || method?.code || "",
      payment_status: payment?.status || "",
      payment_reference: payment?.reference || ""
    }));
    try {
      const orderPayload = await placeOrder({
        payment_reference: payment?.reference,
        guest_email: payerEmail
      });
      sessionStorage.removeItem("vortexus:pendingCheckout");
      sessionStorage.setItem("vortexus:lastOrder", JSON.stringify(orderPayload));
      const orderNumber = orderPayload?.order?.number || orderPayload?.order?.order_number;
      trackStorefrontEvent("order_placed", checkoutMetadata({
        order_number: orderNumber,
        payment_method: payment?.method || method?.code || "",
        payment_status: payment?.status || "",
        payment_reference: payment?.reference || ""
      }));
      notify({ title: "Order placed", message: "Your order has been received.", icon: "task_alt" });
      navigate(`/checkout/confirmation${orderNumber ? `?order_number=${encodeURIComponent(orderNumber)}` : ""}`, { replace: true, state: { orderPayload } });
    } catch {
      trackStorefrontEvent("order_place_failed", checkoutMetadata({
        reason: "place_order_failed",
        payment_method: payment?.method || method?.code || "",
        payment_reference: payment?.reference || ""
      }));
      throw new Error("Order could not be placed.");
    }
  }

  async function handleStatusCheck() {
    if (!activePayment?.reference) return;
    setCheckingStatus(true);
    try {
      const nextPayment = await paymentState.getPaymentStatus(activePayment.reference, activePayment.method);
      setActivePayment(nextPayment);
      trackStorefrontEvent("payment_status_checked", checkoutMetadata({
        payment_method: nextPayment?.method || activePayment.method,
        payment_status: nextPayment?.status || "",
        payment_reference: nextPayment?.reference || activePayment.reference
      }));
      if (isPaymentComplete(nextPayment) || isPaymentFailed(nextPayment)) {
        setConfirmationStartedAt(null);
      }
      storePendingCheckout({
        payment_reference: nextPayment.reference,
        payment: nextPayment,
        method: activeMethod,
        guest_email: guestEmail
      });
      if (isPaymentComplete(nextPayment)) {
        await createOrderFromPayment(nextPayment, activeMethod, guestEmail);
      }
    } catch {
      trackStorefrontEvent("payment_status_checked", checkoutMetadata({
        payment_method: activePayment.method,
        payment_reference: activePayment.reference,
        reason: "status_check_failed"
      }));
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
    trackStorefrontEvent("payment_prompt_retry", checkoutMetadata({
      payment_method: lastPaymentForm.method || "",
      source: "unified_checkout"
    }));
    await handlePaymentSubmit(lastPaymentForm);
  }

  async function submitHighValueDeposit() {
    const normalizedCode = depositCode.trim().toUpperCase();
    if (!normalizedCode) {
      setQuoteError("Enter the M-Pesa confirmation code before submitting.");
      return;
    }

    setQuoteSubmitting(true);
    setQuoteError("");
    setQuoteSuccess("");
    try {
      const payment = await paymentState.initializePayment({
        method: HIGH_VALUE_DEPOSIT_METHOD,
        mpesaCode: normalizedCode,
        phoneNumber: shipping?.address?.phone_number || selectedAddress?.phone_number || user?.phone || user?.phone_number || "",
        payerEmail: user?.email || ""
      });
      const selectedMethod = {
        code: "bank_transfer",
        name: "KCB PayBill Deposit",
        provider: "bank_transfer",
        requires_prepayment: false,
        flow: "offline"
      };
      setActivePayment(payment);
      setActiveMethod(selectedMethod);
      setGuestEmail(user?.email || "");
      storePendingCheckout({
        payment_reference: payment.reference,
        payment,
        method: selectedMethod,
        guest_email: user?.email || ""
      });
      await createOrderFromPayment(payment, selectedMethod, user?.email || "");
      const message = "Payment reference received. Your order is pending account manager confirmation.";
      setQuoteSuccess(message);
      notify({ title: "Pending confirmation", message, icon: "pending_actions" });
      trackStorefrontEvent("checkout_high_value_deposit_submitted", checkoutMetadata({ reason: "mpesa_transaction_limit" }));
    } catch (requestError) {
      const message = requestError.normalized?.message || requestError.message || "Could not submit payment reference.";
      setQuoteError(message);
      notify({ tone: "danger", title: "Payment reference failed", message, icon: "error" });
      trackStorefrontEvent("checkout_high_value_deposit_failed", checkoutMetadata({ reason: "mpesa_transaction_limit" }));
    } finally {
      setQuoteSubmitting(false);
    }
  }

  if (loading || paymentState.loading) return <Spinner label="Loading checkout" />;
  if (!loading && basket?.is_empty) return <Navigate to="/checkout/cart" replace />;

  return (
    <section className="checkout-page">
      <CheckoutStepper current="checkout" basket={basket} shipping={shipping} />
      <div className="checkout-title-row">
        <h1>Checkout</h1>
      </div>

      <Alert>{error || visiblePaymentError}</Alert>

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
                  Change delivery location
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
            <ShippingMethodSelector
              methods={estimatedShippingMethods}
              selectedCode=""
              saving={saving}
              estimated
              title="Estimated delivery"
              note="Exact fees recalculate after you pin and save the delivery location."
            />
          ) : (
            <ShippingMethodSelector
              methods={visibleShippingMethods}
              selectedCode={selectedCode}
              saving={saving}
              onSelect={handleMethodSelect}
            />
          )}

          {activePayment ? (
            <PaymentProgressPanel
              payment={activePayment}
              checking={paymentState.processing || checkingStatus}
              timedOut={paymentTimedOut}
              remainingSeconds={remainingSeconds}
              onCheckStatus={() => void handleStatusCheck()}
              onPromptAgain={() => void handlePromptAgain()}
              onContinue={() => void createOrderFromPayment(activePayment, activeMethod, guestEmail)}
              onChangeMethod={handleChangeMethod}
            />
          ) : shippingReady && !exceedsMpesaLimit ? (
            <PaymentMethodSelector
              methods={paymentState.methods}
              processing={paymentState.processing || saving}
              onSubmit={handlePaymentSubmit}
              submitLabel="Place order"
              defaultEmail={user?.email || ""}
              defaultPhone={user?.phone || user?.phone_number || ""}
            />
          ) : (
            <section className="checkout-card checkout-note-panel delivery-save-required">
              <MaterialIcon name={exceedsMpesaLimit ? "account_balance" : "lock"} size={20} />
              <div>
                <strong>{exceedsMpesaLimit ? "Use KCB PayBill deposit for this order." : "Payment unlocks after delivery is ready."}</strong>
                <span>
                  {exceedsMpesaLimit
                    ? "Pay by PayBill and submit your M-Pesa confirmation code for account manager confirmation."
                    : "Pin your delivery location and select a delivery method to pay and place the order."}
                </span>
              </div>
            </section>
          )}

          {shippingReady && exceedsMpesaLimit ? (
            <button className="primary-button checkout-submit" type="button" disabled={saving} onClick={() => setQuotePromptOpen(true)}>
              <MaterialIcon name="account_balance" size={19} />
              Pay with KCB PayBill
            </button>
          ) : null}
        </div>
        <OrderSummaryPanel basket={basket} shipping={shipping} loading={saving || paymentState.processing || checkingStatus} />
      </div>

      {!lines.length ? <Alert>Your cart is empty.</Alert> : null}
      {quotePromptOpen ? (
        <HighValueQuoteModal
          total={baseOrderTotal}
          depositCode={depositCode}
          onDepositCodeChange={setDepositCode}
          submitting={quoteSubmitting}
          success={quoteSuccess}
          error={quoteError}
          onClose={() => setQuotePromptOpen(false)}
          onSubmit={submitHighValueDeposit}
        />
      ) : null}
    </section>
  );
}

function HighValueQuoteModal({ total, depositCode, onDepositCodeChange, submitting, success, error, onClose, onSubmit }) {
  return (
    <div className="quote-limit-modal" role="dialog" aria-modal="true" aria-labelledby="quote-limit-title">
      <div className="quote-limit-modal__panel">
        <button className="quote-limit-modal__close" type="button" onClick={onClose} aria-label="Close">
          <MaterialIcon name="close" size={18} />
        </button>
        <div className="quote-limit-modal__icon">
          <MaterialIcon name="account_balance" size={28} />
        </div>
        <h2 id="quote-limit-title">Pay by KCB PayBill</h2>
        <p>
          Your order total is {formatCurrency(total, "KES")}. Use PayBill deposit and submit your M-Pesa confirmation code.
        </p>
        <ol className="quote-limit-modal__steps">
          <li>Open the M-PESA menu on your phone.</li>
          <li>Select Lipa na M-PESA, then choose Pay Bill.</li>
          <li>Enter Business Number: <strong>{KCB_PAYBILL_BUSINESS_NUMBER}</strong>.</li>
          <li>Enter Account Number: <strong>{KCB_PAYBILL_ACCOUNT_NUMBER}</strong>.</li>
          <li>Enter the amount: <strong>{formatCurrency(total, "KES")}</strong>.</li>
          <li>Enter your M-PESA PIN and confirm the details.</li>
        </ol>
        <label className="quote-limit-modal__field">
          <span>M-Pesa confirmation code</span>
          <input
            value={depositCode}
            onChange={(event) => onDepositCodeChange(event.target.value.toUpperCase())}
            placeholder="e.g. TH88ABC123"
            autoComplete="off"
          />
          <small>Your order will show pending confirmation until our account manager verifies this code.</small>
        </label>
        <Alert tone="success">{success}</Alert>
        <Alert>{error}</Alert>
        <div className="quote-limit-modal__actions">
          {success ? (
            <button className="primary-button" type="button" onClick={onClose}>
              <MaterialIcon name="check_circle" size={19} />
              Done
            </button>
          ) : (
            <button className="primary-button" type="button" disabled={submitting || !depositCode.trim()} onClick={onSubmit}>
              <MaterialIcon name="pending_actions" size={19} />
              {submitting ? "Submitting..." : "Submit payment reference"}
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
