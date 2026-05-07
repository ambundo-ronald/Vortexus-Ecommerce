import { create } from "zustand";

let nextNotificationId = 1;

export const useUiStore = create((set) => ({
  cartDrawerOpen: false,
  wishlistDrawerOpen: false,
  notifications: [],
  openCartDrawer: () => set({ cartDrawerOpen: true, wishlistDrawerOpen: false }),
  closeCartDrawer: () => set({ cartDrawerOpen: false }),
  openWishlistDrawer: () => set({ wishlistDrawerOpen: true, cartDrawerOpen: false }),
  closeWishlistDrawer: () => set({ wishlistDrawerOpen: false }),
  notify: ({ tone = "success", title = "", message = "", icon = "" } = {}) => {
    const notification = {
      id: nextNotificationId,
      tone,
      title,
      message,
      icon,
      createdAt: Date.now()
    };
    nextNotificationId += 1;
    set((state) => ({
      notifications: [notification, ...state.notifications].slice(0, 4)
    }));
    return notification.id;
  },
  dismissNotification: (id) => {
    set((state) => ({
      notifications: state.notifications.filter((notification) => notification.id !== id)
    }));
  }
}));
