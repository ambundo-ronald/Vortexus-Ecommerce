import { create } from "zustand";

import { checkoutApi } from "../api/checkout.api";

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
      return payload;
    } catch (error) {
      set({ error: error.normalized?.message || error.message, loading: false });
      throw error;
    }
  },

  updateLine: async (lineId, quantity) => {
    set({ loading: true, error: null });
    try {
      const payload = await checkoutApi.updateLine(lineId, { quantity });
      set({ basket: basketFromPayload(payload), loading: false });
      return payload;
    } catch (error) {
      set({ error: error.normalized?.message || error.message, loading: false });
      throw error;
    }
  },

  removeLine: async (lineId) => {
    const { updateLine } = get();
    return updateLine(lineId, 0);
  },

  clearError: () => set({ error: null })
}));
