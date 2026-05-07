import { useCallback, useEffect, useState } from "react";

import { catalogApi } from "../api/catalog.api";

export function useProducts(initialParams = {}, { auto = true } = {}) {
  const [products, setProducts] = useState([]);
  const [pagination, setPagination] = useState(null);
  const [filters, setFilters] = useState(initialParams);
  const [loading, setLoading] = useState(Boolean(auto));
  const [error, setError] = useState(null);

  const fetchProducts = useCallback(async (nextParams = {}) => {
    setLoading(true);
    setError(null);
    try {
      const payload = await catalogApi.products(nextParams);
      setProducts(payload.results || []);
      setPagination(payload.pagination || null);
      setFilters(nextParams);
      return payload;
    } catch (err) {
      setError(err.normalized?.message || err.message);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (auto) void fetchProducts(initialParams);
    // Initial auto-load only. Route-driven pages call fetchProducts when params change.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [auto]);

  return { products, pagination, filters, loading, error, fetchProducts };
}
