import { useCallback, useEffect, useState } from "react";

import { contentApi } from "../api/content.api";

export function useMarketingBlocks(params = {}, { auto = true } = {}) {
  const [blocks, setBlocks] = useState([]);
  const [blocksByPlacement, setBlocksByPlacement] = useState({});
  const [placements, setPlacements] = useState([]);
  const [loading, setLoading] = useState(Boolean(auto));
  const [error, setError] = useState(null);

  const fetchMarketingBlocks = useCallback(async (nextParams = params) => {
    setLoading(true);
    setError(null);
    try {
      const payload = await contentApi.marketingBlocks(nextParams);
      setBlocks(payload.results || []);
      setBlocksByPlacement(payload.by_placement || {});
      setPlacements(payload.placements || []);
      return payload;
    } catch (err) {
      setError(err.normalized?.message || err.message);
      return null;
    } finally {
      setLoading(false);
    }
  }, [params]);

  useEffect(() => {
    if (auto) void fetchMarketingBlocks(params);
    // Initial auto-load only.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [auto]);

  return { blocks, blocksByPlacement, placements, loading, error, fetchMarketingBlocks };
}
