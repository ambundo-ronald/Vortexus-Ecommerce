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
  pendingTwoFactor: null,

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
      if (response?.requires_2fa) {
        set({ pendingTwoFactor: response, initialized: true, loading: false });
        useUiStore.getState().notify({ title: "Check your email", message: "Enter the sign-in code to continue.", icon: "mail" });
        return response;
      }
      set({ user: response?.user || null, initialized: true, loading: false });
      useUiStore.getState().notify({ title: "Signed in", message: "Welcome back.", icon: "login" });
      return response;
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
      useUiStore.getState().notify({ title: "Account created", message: "Check your inbox to verify your email.", icon: "person_add" });
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

  verifyLoginTwoFactor: async (payload) => {
    set({ loading: true, error: "" });
    try {
      const response = await authApi.loginTwoFactor(payload);
      set({ user: response?.user || null, pendingTwoFactor: null, initialized: true, loading: false });
      useUiStore.getState().notify({ title: "Signed in", message: "Welcome back.", icon: "login" });
      return response;
    } catch (error) {
      set({ error: messageFromError(error) || "Invalid verification code.", loading: false });
      throw error;
    }
  },

  verifyEmail: async (payload) => {
    set({ loading: true, error: "" });
    try {
      const response = await authApi.verifyEmail(payload);
      set({ user: response?.user || get().user, loading: false, initialized: true });
      useUiStore.getState().notify({ title: "Email verified", message: "Your account email is confirmed.", icon: "mark_email_read" });
      return response;
    } catch (error) {
      set({ error: messageFromError(error) || "Email verification failed.", loading: false });
      throw error;
    }
  },

  resendEmailVerification: async () => {
    set({ loading: true, error: "" });
    try {
      const response = await authApi.resendEmailVerification();
      set({ user: response?.user || get().user, loading: false, initialized: true });
      useUiStore.getState().notify({ title: "Verification sent", message: "Check your inbox for the new link.", icon: "outgoing_mail" });
      return response;
    } catch (error) {
      set({ error: messageFromError(error) || "Could not send verification email.", loading: false });
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
    set({ user: null, pendingTwoFactor: null, initialized: true, loading: false, error: "" });
    useUiStore.getState().notify({ tone: "info", title: "Signed out", message: "You have been signed out.", icon: "logout" });
  },

  clearError: () => set({ error: "" }),
  clearPendingTwoFactor: () => set({ pendingTwoFactor: null }),
  isAuthenticated: () => Boolean(get().user)
}));
