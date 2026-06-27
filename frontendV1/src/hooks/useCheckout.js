import { useCallback, useEffect, useState } from "react";

import { checkoutApi } from "../api/checkout.api";
import { useCartStore } from "../store/cart.store";
import { checkoutErrorView } from "../utils/checkoutErrors";

export function useCheckout({ auto = true } = {}) {
  const setBasket = useCartStore((state) => state.hydrate);
  const [checkout, setCheckout] = useState(null);
  const [billing, setBilling] = useState(null);
  const [addresses, setAddresses] = useState([]);
  const [loading, setLoading] = useState(Boolean(auto));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [errorView, setErrorView] = useState(null);

  function clearError() {
    setError("");
    setErrorView(null);
  }

  function captureError(error, context) {
    const view = checkoutErrorView(error, context);
    setError(view.message);
    setErrorView(view);
  }

  const loadCheckout = useCallback(async () => {
    setLoading(true);
    clearError();
    try {
      const payload = await checkoutApi.shipping();
      setCheckout(payload);
      checkoutApi.billing().then((billingPayload) => setBilling(billingPayload?.billing || null)).catch(() => {});
      return payload;
    } catch (error) {
      captureError(error, "shipping");
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

  const loadAddresses = useCallback(async () => {
    const payload = await checkoutApi.addresses();
    setAddresses(payload?.results || []);
    return payload?.results || [];
  }, []);

  const saveAddress = useCallback(async (address) => {
    setSaving(true);
    clearError();
    try {
      const payload = await checkoutApi.saveShippingAddress(address);
      setCheckout(payload);
      await setBasket();
      return payload;
    } catch (error) {
      captureError(error, "shipping");
      throw error;
    } finally {
      setSaving(false);
    }
  }, [setBasket]);

  const useShippingAddress = useCallback(async (addressId) => {
    setSaving(true);
    clearError();
    try {
      const payload = await checkoutApi.useShippingAddress({ address_id: addressId });
      setCheckout(payload);
      await setBasket();
      return payload;
    } catch (error) {
      captureError(error, "shipping");
      throw error;
    } finally {
      setSaving(false);
    }
  }, [setBasket]);

  const saveBillingAddress = useCallback(async (address) => {
    setSaving(true);
    clearError();
    try {
      const payload = await checkoutApi.saveBillingAddress(address);
      setBilling(payload?.billing || null);
      return payload;
    } catch (error) {
      captureError(error, "shipping");
      throw error;
    } finally {
      setSaving(false);
    }
  }, []);

  const useBillingAddress = useCallback(async (addressId) => {
    setSaving(true);
    clearError();
    try {
      const payload = await checkoutApi.useBillingAddress({ address_id: addressId });
      setBilling(payload?.billing || null);
      return payload;
    } catch (error) {
      captureError(error, "shipping");
      throw error;
    } finally {
      setSaving(false);
    }
  }, []);

  const selectMethod = useCallback(async (methodCode) => {
    setSaving(true);
    clearError();
    try {
      const payload = await checkoutApi.selectShippingMethod({ method_code: methodCode });
      setCheckout(payload);
      await setBasket();
      return payload;
    } catch (error) {
      captureError(error, "shipping");
      throw error;
    } finally {
      setSaving(false);
    }
  }, [setBasket]);

  const placeOrder = useCallback(async (payload) => {
    setSaving(true);
    clearError();
    try {
      const response = await checkoutApi.placeOrder(payload);
      await setBasket();
      return response;
    } catch (error) {
      captureError(error, "place_order");
      throw error;
    } finally {
      setSaving(false);
    }
  }, [setBasket]);

  const previewCheckout = useCallback(async () => {
    setSaving(true);
    clearError();
    try {
      const payload = await checkoutApi.preview();
      return payload?.preview || null;
    } catch (error) {
      captureError(error, "preview");
      throw error;
    } finally {
      setSaving(false);
    }
  }, []);

  const loadOrderConfirmation = useCallback(async (orderNumber) => {
    setLoading(true);
    clearError();
    try {
      return await checkoutApi.thankYou(orderNumber);
    } catch (error) {
      captureError(error, "confirmation");
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (auto) void loadCheckout();
  }, [auto, loadCheckout]);

  return {
    checkout,
    basket: checkout?.basket || null,
    shipping: checkout?.shipping || null,
    billing,
    addresses,
    loading,
    saving,
    error,
    errorView,
    setError,
    setErrorView,
    clearError,
    loadCheckout,
    loadAddresses,
    saveAddress,
    useShippingAddress,
    saveBillingAddress,
    useBillingAddress,
    selectMethod,
    previewCheckout,
    placeOrder,
    loadOrderConfirmation
  };
}
