import { useCallback, useEffect, useState } from "react";

import { ordersApi } from "../api/orders.api";
import { useCartStore } from "../store/cart.store";

function messageFromError(error) {
  return error?.normalized?.message || error?.message || "Could not load orders.";
}

export function useOrders({ auto = true, page = 1, pageSize = 20 } = {}) {
  const hydrateCart = useCartStore((state) => state.hydrate);
  const [orders, setOrders] = useState([]);
  const [pagination, setPagination] = useState(null);
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(Boolean(auto));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const loadOrders = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await ordersApi.list({ page, page_size: pageSize });
      setOrders(payload?.results || []);
      setPagination(payload?.pagination || null);
      return payload;
    } catch (error) {
      setError(messageFromError(error));
      throw error;
    } finally {
      setLoading(false);
    }
  }, [page, pageSize]);

  const loadOrder = useCallback(async (orderNumber) => {
    setLoading(true);
    setError("");
    try {
      const payload = await ordersApi.detail(orderNumber);
      setOrder(payload?.order || null);
      return payload?.order || null;
    } catch (error) {
      setError(messageFromError(error));
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

  const reorder = useCallback(async (orderNumber) => {
    setSaving(true);
    setError("");
    try {
      const payload = await ordersApi.reorder(orderNumber);
      await hydrateCart();
      return payload;
    } catch (error) {
      setError(messageFromError(error));
      throw error;
    } finally {
      setSaving(false);
    }
  }, [hydrateCart]);

  useEffect(() => {
    if (auto) void loadOrders();
  }, [auto, loadOrders]);

  return {
    orders,
    pagination,
    order,
    loading,
    saving,
    error,
    loadOrders,
    loadOrder,
    reorder
  };
}
