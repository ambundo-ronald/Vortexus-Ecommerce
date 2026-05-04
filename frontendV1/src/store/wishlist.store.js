import { create } from "zustand";

import { wishlistApi } from "../api/wishlist.api";

function messageFromError(error) {
  return error?.normalized?.message || error?.message || "Wishlist update failed.";
}

export const useWishlistStore = create((set, get) => ({
  statusByProductId: {},
  loading: false,
  savingIds: {},
  error: "",

  loadStatus: async (productIds = []) => {
    const ids = [...new Set(productIds.map(Number).filter(Boolean))];
    if (!ids.length) return {};
    set({ loading: true, error: "" });
    try {
      const payload = await wishlistApi.status({ product_ids: ids });
      const nextStatus = {};
      for (const item of payload?.results || []) {
        nextStatus[item.product_id] = Boolean(item.in_wishlist);
      }
      set((state) => ({
        statusByProductId: { ...state.statusByProductId, ...nextStatus },
        loading: false
      }));
      return nextStatus;
    } catch (error) {
      set({ loading: false, error: messageFromError(error) });
      return {};
    }
  },

  add: async (productId) => {
    const id = Number(productId);
    set((state) => ({ savingIds: { ...state.savingIds, [id]: true }, error: "" }));
    try {
      await wishlistApi.addDefaultItem({ product_id: id, quantity: 1 });
      set((state) => ({
        statusByProductId: { ...state.statusByProductId, [id]: true },
        savingIds: { ...state.savingIds, [id]: false }
      }));
    } catch (error) {
      set((state) => ({ savingIds: { ...state.savingIds, [id]: false }, error: messageFromError(error) }));
      throw error;
    }
  },

  remove: async (productId) => {
    const id = Number(productId);
    set((state) => ({ savingIds: { ...state.savingIds, [id]: true }, error: "" }));
    try {
      await wishlistApi.removeDefaultItem(id);
      set((state) => ({
        statusByProductId: { ...state.statusByProductId, [id]: false },
        savingIds: { ...state.savingIds, [id]: false }
      }));
    } catch (error) {
      set((state) => ({ savingIds: { ...state.savingIds, [id]: false }, error: messageFromError(error) }));
      throw error;
    }
  },

  toggle: async (productId) => {
    const id = Number(productId);
    const inWishlist = Boolean(get().statusByProductId[id]);
    if (inWishlist) return get().remove(id);
    return get().add(id);
  },

  setStatus: (productId, inWishlist) => {
    const id = Number(productId);
    set((state) => ({
      statusByProductId: { ...state.statusByProductId, [id]: Boolean(inWishlist) }
    }));
  }
}));
