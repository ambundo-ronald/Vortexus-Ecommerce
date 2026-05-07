import { useCallback, useEffect, useState } from "react";

import { catalogApi } from "../api/catalog.api";

export function useProductDetail(productId, { auto = true } = {}) {
  const [product, setProduct] = useState(null);
  const [related, setRelated] = useState([]);
  const [loading, setLoading] = useState(Boolean(auto && productId));
  const [error, setError] = useState(null);

  const fetchProduct = useCallback(async (id = productId) => {
    if (!id) return null;
    setLoading(true);
    setError(null);
    try {
      const payload = await catalogApi.product(id);
      setProduct(payload.product || null);
      setRelated(payload.related || []);
      return payload;
    } catch (err) {
      setError(err.normalized?.message || err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [productId]);

  useEffect(() => {
    if (auto && productId) void fetchProduct(productId);
  }, [auto, fetchProduct, productId]);

  return { product, related, loading, error, fetchProduct };
}
