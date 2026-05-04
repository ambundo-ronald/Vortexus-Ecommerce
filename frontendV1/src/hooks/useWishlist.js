import { useCallback, useEffect, useState } from "react";

import { wishlistApi } from "../api/wishlist.api";
import { useWishlistStore } from "../store/wishlist.store";

function messageFromError(error) {
  return error?.normalized?.message || error?.message || "Could not load wishlist.";
}

export function useWishlist({ auto = true } = {}) {
  const [wishlist, setWishlist] = useState(null);
  const [loading, setLoading] = useState(Boolean(auto));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const loadWishlist = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await wishlistApi.defaultList();
      setWishlist(payload?.wishlist || null);
      return payload?.wishlist || null;
    } catch (error) {
      setError(messageFromError(error));
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

  const removeItem = useCallback(async (productId) => {
    setSaving(true);
    setError("");
    try {
      const payload = await wishlistApi.removeDefaultItem(productId);
      setWishlist(payload?.wishlist || null);
      useWishlistStore.getState().setStatus(productId, false);
      return payload?.wishlist || null;
    } catch (error) {
      setError(messageFromError(error));
      throw error;
    } finally {
      setSaving(false);
    }
  }, []);

  useEffect(() => {
    if (auto) void loadWishlist();
  }, [auto, loadWishlist]);

  return {
    wishlist,
    items: wishlist?.items || [],
    loading,
    saving,
    error,
    loadWishlist,
    removeItem
  };
}
