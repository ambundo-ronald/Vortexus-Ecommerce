import { useCallback, useEffect, useState } from "react";

import { checkoutApi } from "../api/checkout.api";
import { useCartStore } from "../store/cart.store";

function messageFromError(error) {
  return error?.normalized?.message || error?.message || "Something went wrong. Try again.";
}

export function useCheckout({ auto = true } = {}) {
  const setBasket = useCartStore((state) => state.hydrate);
  const [checkout, setCheckout] = useState(null);
  const [billing, setBilling] = useState(null);
  const [addresses, setAddresses] = useState([]);
  const [loading, setLoading] = useState(Boolean(auto));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const loadCheckout = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await checkoutApi.shipping();
      setCheckout(payload);
      checkoutApi.billing().then((billingPayload) => setBilling(billingPayload?.billing || null)).catch(() => {});
      return payload;
    } catch (error) {
      setError(messageFromError(error));
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
    setError("");
    try {
      const payload = await checkoutApi.saveShippingAddress(address);
      setCheckout(payload);
      await setBasket();
      return payload;
    } catch (error) {
      setError(messageFromError(error));
      throw error;
    } finally {
      setSaving(false);
    }
  }, [setBasket]);

  const useShippingAddress = useCallback(async (addressId) => {
    setSaving(true);
    setError("");
    try {
      const payload = await checkoutApi.useShippingAddress({ address_id: addressId });
      setCheckout(payload);
      await setBasket();
      return payload;
    } catch (error) {
      setError(messageFromError(error));
      throw error;
    } finally {
      setSaving(false);
    }
  }, [setBasket]);

  const saveBillingAddress = useCallback(async (address) => {
    setSaving(true);
    setError("");
    try {
      const payload = await checkoutApi.saveBillingAddress(address);
      setBilling(payload?.billing || null);
      return payload;
    } catch (error) {
      setError(messageFromError(error));
      throw error;
    } finally {
      setSaving(false);
    }
  }, []);

  const useBillingAddress = useCallback(async (addressId) => {
    setSaving(true);
    setError("");
    try {
      const payload = await checkoutApi.useBillingAddress({ address_id: addressId });
      setBilling(payload?.billing || null);
      return payload;
    } catch (error) {
      setError(messageFromError(error));
      throw error;
    } finally {
      setSaving(false);
    }
  }, []);

  const selectMethod = useCallback(async (methodCode) => {
    setSaving(true);
    setError("");
    try {
      const payload = await checkoutApi.selectShippingMethod({ method_code: methodCode });
      setCheckout(payload);
      await setBasket();
      return payload;
    } catch (error) {
      setError(messageFromError(error));
      throw error;
    } finally {
      setSaving(false);
    }
  }, [setBasket]);

  const placeOrder = useCallback(async (payload) => {
    setSaving(true);
    setError("");
    try {
      const response = await checkoutApi.placeOrder(payload);
      await setBasket();
      return response;
    } catch (error) {
      setError(messageFromError(error));
      throw error;
    } finally {
      setSaving(false);
    }
  }, [setBasket]);

  const previewCheckout = useCallback(async () => {
    setSaving(true);
    setError("");
    try {
      const payload = await checkoutApi.preview();
      return payload?.preview || null;
    } catch (error) {
      setError(messageFromError(error));
      throw error;
    } finally {
      setSaving(false);
    }
  }, []);

  const loadOrderConfirmation = useCallback(async (orderNumber) => {
    setLoading(true);
    setError("");
    try {
      return await checkoutApi.thankYou(orderNumber);
    } catch (error) {
      setError(messageFromError(error));
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
    setError,
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
