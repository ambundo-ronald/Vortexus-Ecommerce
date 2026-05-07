import { create } from "zustand";

import { authApi } from "../api/auth.api";

function messageFromError(error) {
  if (error?.normalized?.status === 403) return "";
  const fieldMessage = fieldErrors(error?.response?.data);
  if (fieldMessage) return fieldMessage;
  return error?.normalized?.message || error?.message || "Authentication failed.";
}

function fieldErrors(payload) {
  if (!payload || typeof payload !== "object") return "";
  const entries = Object.entries(payload).filter(([, value]) => Array.isArray(value) || typeof value === "string");
  if (!entries.length) return "";
  const [field, value] = entries[0];
  const message = Array.isArray(value) ? value[0] : value;
  if (!message) return "";
  return `${field.replaceAll("_", " ")}: ${message}`;
}

export const useAuthStore = create((set, get) => ({
  user: null,
  initialized: false,
  loading: false,
  error: "",

  loadUser: async ({ silent = true } = {}) => {
    set({ loading: !silent, error: "" });
    try {
      const payload = await authApi.me();
      set({ user: payload?.user || null, initialized: true, loading: false });
      return payload?.user || null;
    } catch (error) {
      set({ user: null, initialized: true, loading: false, error: messageFromError(error) });
      return null;
    }
  },

  login: async (payload) => {
    set({ loading: true, error: "" });
    try {
      const response = await authApi.login(payload);
      set({ user: response?.user || null, initialized: true, loading: false });
      return response?.user || null;
    } catch (error) {
      const message = messageFromError(error) || "Invalid email or password.";
      set({ error: message, loading: false });
      throw error;
    }
  },

  register: async (payload) => {
    set({ loading: true, error: "" });
    try {
      const response = await authApi.register(payload);
      set({ user: response?.user || null, initialized: true, loading: false });
      return response?.user || null;
    } catch (error) {
      set({ error: messageFromError(error) || "Registration failed.", loading: false });
      throw error;
    }
  },

  updateProfile: async (payload) => {
    set({ loading: true, error: "" });
    try {
      const response = await authApi.updateProfile(payload);
      set({ user: response?.user || null, loading: false, initialized: true });
      return response?.user || null;
    } catch (error) {
      set({ error: messageFromError(error) || "Profile update failed.", loading: false });
      throw error;
    }
  },

  logout: async () => {
    set({ loading: true, error: "" });
    try {
      await authApi.logout();
    } catch {
      // Local session state should still clear if the server session is already gone.
    }
    set({ user: null, initialized: true, loading: false, error: "" });
  },

  clearError: () => set({ error: "" }),
  isAuthenticated: () => Boolean(get().user)
}));
