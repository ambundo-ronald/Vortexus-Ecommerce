import { useCallback, useEffect, useState } from "react";

import { catalogApi } from "../api/catalog.api";

export function useCategories({ auto = true } = {}) {
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(Boolean(auto));
  const [error, setError] = useState(null);

  const fetchCategories = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = await catalogApi.categories();
      const nextCategories = Array.isArray(payload) ? payload : payload.results || [];
      setCategories(nextCategories);
      return payload;
    } catch (err) {
      setError(err.normalized?.message || err.message);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (auto) void fetchCategories();
  }, [auto, fetchCategories]);

  return { categories, loading, error, fetchCategories };
}
