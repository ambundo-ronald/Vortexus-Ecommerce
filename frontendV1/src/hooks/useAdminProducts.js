import { useCallback, useState } from "react";

import { adminProductsApi } from "../api/adminProducts.api";

export function useAdminProducts() {
  const [state, setState] = useState({ products: [], pagination: null, loading: false, error: null });

  const fetchProducts = useCallback(async (params) => {
    setState((current) => ({ ...current, loading: true, error: null }));
    try {
      const payload = await adminProductsApi.list(params);
      setState({ products: payload.results || [], pagination: payload.pagination || null, loading: false, error: null });
      return payload;
    } catch (error) {
      setState((current) => ({ ...current, loading: false, error }));
      throw error;
    }
  }, []);

  return { ...state, fetchProducts };
}
