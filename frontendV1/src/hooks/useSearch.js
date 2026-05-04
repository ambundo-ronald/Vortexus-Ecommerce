import { useCallback, useState } from "react";

import { searchApi } from "../api/search.api";

export function useSearch() {
  const [results, setResults] = useState([]);
  const [pagination, setPagination] = useState(null);
  const [source, setSource] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const search = useCallback(async (params) => {
    setLoading(true);
    setError(null);
    try {
      const payload = await searchApi.text(params);
      setResults(payload.results || []);
      setPagination(payload.pagination || null);
      setSource(payload.source || "");
      return payload;
    } catch (err) {
      setError(err.normalized?.message || err.message);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const setSearchResults = useCallback((payload) => {
    setResults(payload?.results || []);
    setPagination(payload?.pagination || null);
    setSource(payload?.source || "");
    setError(null);
  }, []);

  return { results, pagination, source, loading, error, search, setSearchResults };
}
