import { useCallback, useEffect, useState } from "react";

import { wishlistApi } from "../api/wishlist.api";
import { useUiStore } from "../store/ui.store";
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
      useUiStore.getState().notify({
        title: "Removed",
        message: "The product was removed from your wishlist.",
        icon: "heart_minus"
      });
      return payload?.wishlist || null;
    } catch (error) {
      setError(messageFromError(error));
      throw error;
    } finally {
      setSaving(false);
    }
  }, []);

  const shareWishlist = useCallback(async ({ regenerate = false } = {}) => {
    if (!wishlist?.id) return null;
    setSaving(true);
    setError("");
    try {
      const payload = await wishlistApi.share(wishlist.id, {
        visibility: "Shared",
        regenerate_key: regenerate
      });
      setWishlist(payload?.wishlist || wishlist);
      useUiStore.getState().notify({
        title: regenerate ? "Share link refreshed" : "Share link ready",
        message: "You can share this wishlist with customers or your team.",
        icon: "ios_share"
      });
      return payload;
    } catch (error) {
      setError(messageFromError(error));
      throw error;
    } finally {
      setSaving(false);
    }
  }, [wishlist]);

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
    removeItem,
    shareWishlist
  };
}
