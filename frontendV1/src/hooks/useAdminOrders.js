import { useCallback, useState } from "react";

import { adminOrdersApi } from "../api/adminOrders.api";

export function useAdminOrders() {
  const [state, setState] = useState({ orders: [], pagination: null, summary: null, loading: false, error: null });

  const fetchOrders = useCallback(async (params) => {
    setState((current) => ({ ...current, loading: true, error: null }));
    try {
      const payload = await adminOrdersApi.list(params);
      setState({
        orders: payload.results || [],
        pagination: payload.pagination || null,
        summary: payload.summary || null,
        loading: false,
        error: null
      });
      return payload;
    } catch (error) {
      setState((current) => ({ ...current, loading: false, error }));
      throw error;
    }
  }, []);

  return { ...state, fetchOrders };
}
