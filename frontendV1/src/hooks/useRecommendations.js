import { useCallback, useEffect, useState } from "react";

import { recommendationsApi } from "../api/recommendations.api";

export function useRecommendations(params = { limit: 8 }, { auto = true } = {}) {
  const [recommendations, setRecommendations] = useState([]);
  const [strategy, setStrategy] = useState("");
  const [loading, setLoading] = useState(Boolean(auto));
  const [error, setError] = useState(null);

  const fetchRecommendations = useCallback(async (nextParams = params) => {
    setLoading(true);
    setError(null);
    try {
      const payload = await recommendationsApi.list(nextParams);
      setRecommendations(payload.results || []);
      setStrategy(payload.strategy || "");
      return payload;
    } catch (err) {
      setError(err.normalized?.message || err.message);
      return null;
    } finally {
      setLoading(false);
    }
  }, [params]);

  useEffect(() => {
    if (auto) void fetchRecommendations(params);
    // Initial auto-load only.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [auto]);

  return { recommendations, strategy, loading, error, fetchRecommendations };
}
