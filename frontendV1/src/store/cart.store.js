import { create } from "zustand";

import { checkoutApi } from "../api/checkout.api";
import { useUiStore } from "./ui.store";

const emptyBasket = {
  lines: [],
  line_count: 0,
  item_count: 0,
  totals: { subtotal: 0, currency: "USD" },
  is_empty: true,
  shipping_required: false
};

function addItemErrorTitle(message = "") {
  if (message.toLowerCase().includes("different currency")) return "Cart currency mismatch";
  if (message.toLowerCase().includes("out of stock") || message.toLowerCase().includes("available")) return "Not enough stock";
  return "Could not add item";
}

function basketFromPayload(payload) {
  return payload?.basket || emptyBasket;
}

function savedFromPayload(payload) {
  return payload?.saved?.results || payload?.results || [];
}

export const useCartStore = create((set, get) => ({
  basket: emptyBasket,
  savedItems: [],
  loading: false,
  savedLoading: false,
  error: null,

  hydrate: async () => {
    set({ loading: true, error: null });
    try {
      const payload = await checkoutApi.basket();
      set({ basket: basketFromPayload(payload), loading: false });
      return payload;
    } catch (error) {
      set({ error: error.normalized?.message || error.message, loading: false });
      throw error;
    }
  },

  addItem: async (productId, quantity = 1, options = []) => {
    set({ loading: true, error: null });
    try {
      const payload = await checkoutApi.addItem({ product_id: productId, quantity, options });
      set({ basket: basketFromPayload(payload), loading: false });
      useUiStore.getState().notify({
        title: "Added to cart",
        message: "The product is ready in your cart.",
        icon: "add_shopping_cart"
      });
      return payload;
    } catch (error) {
      const message = error.normalized?.message || error.message;
      set({ error: message, loading: false });
      useUiStore.getState().notify({ tone: "warning", title: addItemErrorTitle(message), message });
      throw error;
    }
  },

  updateLine: async (lineId, quantity, options = {}) => {
    set({ loading: true, error: null });
    try {
      const payload = await checkoutApi.updateLine(lineId, { quantity });
      set({ basket: basketFromPayload(payload), loading: false });
      useUiStore.getState().notify({
        title: options.successTitle || "Cart updated",
        message: options.successMessage || "Your cart has been updated.",
        icon: quantity > 0 ? "shopping_cart" : "remove_shopping_cart"
      });
      return payload;
    } catch (error) {
      const message = error.normalized?.message || error.message;
      set({ error: message, loading: false });
      useUiStore.getState().notify({ tone: "danger", title: "Cart update failed", message });
      throw error;
    }
  },

  removeLine: async (lineId) => {
    const { updateLine } = get();
    return updateLine(lineId, 0, {
      successTitle: "Removed from cart",
      successMessage: "The item was removed."
    });
  },

  loadSavedItems: async () => {
    set({ savedLoading: true, error: null });
    try {
      const payload = await checkoutApi.savedItems();
      set({ savedItems: savedFromPayload(payload), savedLoading: false });
      return payload;
    } catch (error) {
      const message = error.normalized?.message || error.message;
      set({ error: message, savedLoading: false });
      throw error;
    }
  },

  saveLineForLater: async (lineId) => {
    set({ loading: true, error: null });
    try {
      const payload = await checkoutApi.saveForLater(lineId);
      set({ basket: basketFromPayload(payload), savedItems: savedFromPayload(payload), loading: false });
      useUiStore.getState().notify({
        title: "Saved for later",
        message: "The item moved out of your cart.",
        icon: "bookmark_added"
      });
      return payload;
    } catch (error) {
      const message = error.normalized?.message || error.message;
      set({ error: message, loading: false });
      useUiStore.getState().notify({ tone: "danger", title: "Could not save item", message });
      throw error;
    }
  },

  moveSavedToCart: async (savedLineId) => {
    set({ loading: true, error: null });
    try {
      const payload = await checkoutApi.moveSavedToCart(savedLineId);
      set({ basket: basketFromPayload(payload), savedItems: savedFromPayload(payload), loading: false });
      useUiStore.getState().notify({
        title: "Moved to cart",
        message: "The item is ready in your cart.",
        icon: "add_shopping_cart"
      });
      return payload;
    } catch (error) {
      const message = error.normalized?.message || error.message;
      set({ error: message, loading: false });
      useUiStore.getState().notify({ tone: "danger", title: "Could not move item", message });
      throw error;
    }
  },

  removeSavedItem: async (savedLineId) => {
    set({ savedLoading: true, error: null });
    try {
      const payload = await checkoutApi.removeSavedItem(savedLineId);
      set({ savedItems: savedFromPayload(payload), savedLoading: false });
      useUiStore.getState().notify({
        title: "Removed",
        message: "The saved item was removed.",
        icon: "bookmark_remove"
      });
      return payload;
    } catch (error) {
      const message = error.normalized?.message || error.message;
      set({ error: message, savedLoading: false });
      useUiStore.getState().notify({ tone: "danger", title: "Could not remove saved item", message });
      throw error;
    }
  },

  applyVoucher: async (code) => {
    set({ loading: true, error: null });
    try {
      const payload = await checkoutApi.applyVoucher({ code });
      set({ basket: basketFromPayload(payload), loading: false });
      useUiStore.getState().notify({
        title: "Coupon applied",
        message: "Your cart has been updated.",
        icon: "sell"
      });
      return payload;
    } catch (error) {
      const message = error.normalized?.message || error.message;
      set({ error: message, loading: false });
      useUiStore.getState().notify({ tone: "warning", title: "Coupon not applied", message });
      throw error;
    }
  },

  removeVoucher: async (voucherId) => {
    set({ loading: true, error: null });
    try {
      const payload = await checkoutApi.removeVoucher(voucherId);
      set({ basket: basketFromPayload(payload), loading: false });
      useUiStore.getState().notify({
        title: "Coupon removed",
        message: "Your cart has been updated.",
        icon: "sell"
      });
      return payload;
    } catch (error) {
      const message = error.normalized?.message || error.message;
      set({ error: message, loading: false });
      useUiStore.getState().notify({ tone: "warning", title: "Could not remove coupon", message });
      throw error;
    }
  },

  clearError: () => set({ error: null })
}));
