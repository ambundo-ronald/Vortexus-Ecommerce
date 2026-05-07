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

function basketFromPayload(payload) {
  return payload?.basket || emptyBasket;
}

export const useCartStore = create((set, get) => ({
  basket: emptyBasket,
  loading: false,
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

  addItem: async (productId, quantity = 1) => {
    set({ loading: true, error: null });
    try {
      const payload = await checkoutApi.addItem({ product_id: productId, quantity });
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
      useUiStore.getState().notify({ tone: "danger", title: "Could not add item", message });
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

  clearError: () => set({ error: null })
}));
