import { useCallback, useEffect, useState } from "react";

import { searchApi } from "../api/search.api";

export function useSearchFacets({ auto = true } = {}) {
  const [facets, setFacets] = useState({ categories: [], brands: [], price_ranges: [], availability: [] });
  const [loading, setLoading] = useState(Boolean(auto));
  const [error, setError] = useState(null);

  const loadFacets = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = await searchApi.facets();
      const nextFacets = payload?.facets || {};
      setFacets({
        categories: nextFacets.categories || [],
        brands: nextFacets.brands || [],
        price_ranges: nextFacets.price_ranges || [],
        availability: nextFacets.availability || []
      });
      return nextFacets;
    } catch (err) {
      setError(err.normalized?.message || err.message);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (auto) void loadFacets();
  }, [auto, loadFacets]);

  return { facets, loading, error, loadFacets };
}
