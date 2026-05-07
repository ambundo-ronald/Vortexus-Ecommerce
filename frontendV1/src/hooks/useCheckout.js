import { useCallback, useEffect, useState } from "react";

import { checkoutApi } from "../api/checkout.api";
import { useCartStore } from "../store/cart.store";

function messageFromError(error) {
  return error?.normalized?.message || error?.message || "Something went wrong. Try again.";
}

export function useCheckout({ auto = true } = {}) {
  const setBasket = useCartStore((state) => state.hydrate);
  const [checkout, setCheckout] = useState(null);
  const [loading, setLoading] = useState(Boolean(auto));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const loadCheckout = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await checkoutApi.shipping();
      setCheckout(payload);
      return payload;
    } catch (error) {
      setError(messageFromError(error));
      throw error;
    } finally {
      setLoading(false);
    }
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

  useEffect(() => {
    if (auto) void loadCheckout();
  }, [auto, loadCheckout]);

  return {
    checkout,
    basket: checkout?.basket || null,
    shipping: checkout?.shipping || null,
    loading,
    saving,
    error,
    setError,
    loadCheckout,
    saveAddress,
    selectMethod,
    placeOrder
  };
}
