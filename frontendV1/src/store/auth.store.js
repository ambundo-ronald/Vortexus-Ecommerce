import { create } from "zustand";

import { authApi } from "../api/auth.api";
import { useUiStore } from "./ui.store";

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
      useUiStore.getState().notify({ title: "Signed in", message: "Welcome back.", icon: "login" });
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
      useUiStore.getState().notify({ title: "Account created", message: "Your account is ready.", icon: "person_add" });
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
      useUiStore.getState().notify({ title: "Profile saved", message: "Your account details were updated.", icon: "manage_accounts" });
      return response?.user || null;
    } catch (error) {
      set({ error: messageFromError(error) || "Profile update failed.", loading: false });
      throw error;
    }
  },

  changePassword: async (payload) => {
    set({ loading: true, error: "" });
    try {
      const response = await authApi.changePassword(payload);
      set({ loading: false, error: "" });
      useUiStore.getState().notify({ title: "Password changed", message: "Your password was updated.", icon: "lock_reset" });
      return response;
    } catch (error) {
      set({ error: messageFromError(error) || "Password change failed.", loading: false });
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
    useUiStore.getState().notify({ tone: "info", title: "Signed out", message: "You have been signed out.", icon: "logout" });
  },

  clearError: () => set({ error: "" }),
  isAuthenticated: () => Boolean(get().user)
}));
