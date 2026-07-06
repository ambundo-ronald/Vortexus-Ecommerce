import { useCallback, useEffect, useState } from "react";

import { storefrontExtrasApi } from "../api/storefrontExtras.api";

export function useRecentlyBought(params = { limit: 8 }, { auto = true } = {}) {
  const [products, setProducts] = useState([]);
  const [strategy, setStrategy] = useState("");
  const [loading, setLoading] = useState(Boolean(auto));
  const [reordering, setReordering] = useState(false);
  const [error, setError] = useState(null);

  const fetchRecentlyBought = useCallback(async (nextParams = params) => {
    setLoading(true);
    setError(null);
    try {
      const payload = await storefrontExtrasApi.account.recentlyBought(nextParams);
      setProducts(payload.results || []);
      setStrategy(payload.strategy || "");
      return payload;
    } catch (err) {
      setError(err.normalized?.message || err.message);
      setProducts([]);
      return null;
    } finally {
      setLoading(false);
    }
  }, [params]);

  const reorderRecentlyBought = useCallback(async (nextParams = params) => {
    setReordering(true);
    setError(null);
    try {
      return await storefrontExtrasApi.account.reorderRecentlyBought(nextParams);
    } catch (err) {
      setError(err.normalized?.message || err.message);
      throw err;
    } finally {
      setReordering(false);
    }
  }, [params]);

  useEffect(() => {
    if (auto) void fetchRecentlyBought(params);
    // Initial auto-load only.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [auto]);

  return { products, strategy, loading, reordering, error, fetchRecentlyBought, reorderRecentlyBought };
}
