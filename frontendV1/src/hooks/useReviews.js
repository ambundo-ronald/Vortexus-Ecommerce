import { useCallback, useEffect, useState } from "react";

import { reviewsApi } from "../api/reviews.api";

function messageFromError(error) {
  const payload = error?.response?.data;
  const field = payload && typeof payload === "object" ? Object.entries(payload).find(([, value]) => Array.isArray(value) || typeof value === "string") : null;
  if (field) {
    const [name, value] = field;
    return `${name.replaceAll("_", " ")}: ${Array.isArray(value) ? value[0] : value}`;
  }
  return error?.normalized?.message || error?.message || "Could not load reviews.";
}

export function useProductReviews(productId, { auto = true } = {}) {
  const [reviews, setReviews] = useState([]);
  const [summary, setSummary] = useState(null);
  const [yourReview, setYourReview] = useState(null);
  const [loading, setLoading] = useState(Boolean(auto));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const loadReviews = useCallback(async () => {
    if (!productId) return null;
    setLoading(true);
    setError("");
    try {
      const payload = await reviewsApi.productReviews(productId);
      setReviews(payload?.results || []);
      setSummary(payload?.summary || null);
      setYourReview(payload?.your_review || null);
      return payload;
    } catch (error) {
      setError(messageFromError(error));
      throw error;
    } finally {
      setLoading(false);
    }
  }, [productId]);

  const createReview = useCallback(async (payload) => {
    setSaving(true);
    setError("");
    try {
      const response = await reviewsApi.createProductReview(productId, payload);
      setYourReview(response?.review || null);
      setSummary(response?.summary || null);
      await loadReviews();
      return response?.review || null;
    } catch (error) {
      setError(messageFromError(error));
      throw error;
    } finally {
      setSaving(false);
    }
  }, [loadReviews, productId]);

  useEffect(() => {
    if (auto) void loadReviews();
  }, [auto, loadReviews]);

  return { reviews, summary, yourReview, loading, saving, error, loadReviews, createReview };
}

export function useAccountReviews({ auto = true, status = "" } = {}) {
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(Boolean(auto));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const loadReviews = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await reviewsApi.accountReviews(status ? { status } : undefined);
      setReviews(payload?.results || []);
      return payload?.results || [];
    } catch (error) {
      setError(messageFromError(error));
      throw error;
    } finally {
      setLoading(false);
    }
  }, [status]);

  const updateReview = useCallback(async (reviewId, payload) => {
    setSaving(true);
    setError("");
    try {
      const response = await reviewsApi.updateAccountReview(reviewId, payload);
      await loadReviews();
      return response?.review || null;
    } catch (error) {
      setError(messageFromError(error));
      throw error;
    } finally {
      setSaving(false);
    }
  }, [loadReviews]);

  const removeReview = useCallback(async (reviewId) => {
    setSaving(true);
    setError("");
    try {
      await reviewsApi.removeAccountReview(reviewId);
      setReviews((current) => current.filter((review) => review.id !== reviewId));
    } catch (error) {
      setError(messageFromError(error));
      throw error;
    } finally {
      setSaving(false);
    }
  }, []);

  useEffect(() => {
    if (auto) void loadReviews();
  }, [auto, loadReviews]);

  return { reviews, loading, saving, error, loadReviews, updateReview, removeReview };
}
