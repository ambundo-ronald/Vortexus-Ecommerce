import { useCallback, useEffect, useState } from "react";

import { catalogApi } from "../api/catalog.api";
import { productId, productSlug, productTitle } from "../utils/productDisplay";

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
      const payload = await fetchProductWithFallback(id);
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

async function fetchProductWithFallback(reference) {
  try {
    return await catalogApi.product(reference);
  } catch (error) {
    if (isNumericReference(reference)) throw error;

    const fallbackProduct = await findProductFromReadablePath(reference);
    const fallbackProductId = productId(fallbackProduct);
    if (!fallbackProductId) throw error;

    return catalogApi.product(fallbackProductId);
  }
}

async function findProductFromReadablePath(reference) {
  const query = readableQuery(reference);
  if (!query) return null;

  const payload = await catalogApi.products({ q: query, page_size: 24 });
  const products = payload.results || [];
  const normalizedReference = normalizeSlug(reference);

  return (
    products.find((product) => normalizeSlug(productSlug(product)) === normalizedReference) ||
    products.find((product) => normalizeSlug(productTitle(product, "")) === normalizedReference) ||
    products[0] ||
    null
  );
}

function readableQuery(reference) {
  return String(reference || "")
    .split("/")
    .filter(Boolean)
    .pop()
    ?.replace(/-/g, " ")
    .trim() || "";
}

function normalizeSlug(value = "") {
  return String(value || "")
    .trim()
    .toLowerCase()
    .replace(/&/g, " and ")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function isNumericReference(reference) {
  return /^\d+$/.test(String(reference || "").trim());
}
