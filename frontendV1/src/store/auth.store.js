import { create } from "zustand";

import { authApi } from "../api/auth.api";
import { useUiStore } from "./ui.store";

function messageFromError(error) {
  if (error?.normalized?.status === 403 && error?.normalized?.code !== "account_inactive") return "";
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
  errorCode: "",
  pendingTwoFactor: null,

  loadUser: async ({ silent = true } = {}) => {
    set({ loading: !silent, error: "", errorCode: "" });
    try {
      const payload = await authApi.me();
      set({ user: payload?.user || null, initialized: true, loading: false });
      return payload?.user || null;
    } catch (error) {
      set({ user: null, initialized: true, loading: false, error: messageFromError(error), errorCode: error?.normalized?.code || "" });
      return null;
    }
  },

  login: async (payload) => {
    set({ loading: true, error: "", errorCode: "" });
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
      set({ error: message, errorCode: error?.normalized?.code || "", loading: false });
      throw error;
    }
  },

  register: async (payload) => {
    set({ loading: true, error: "", errorCode: "" });
    try {
      const response = await authApi.register(payload);
      set({ user: response?.user || null, initialized: true, loading: false });
      useUiStore.getState().notify({ title: "Account created", message: "Check your inbox to verify your email.", icon: "person_add" });
      return response?.user || null;
    } catch (error) {
      set({ error: messageFromError(error) || "Registration failed.", errorCode: error?.normalized?.code || "", loading: false });
      throw error;
    }
  },

  requestReactivation: async (payload) => {
    set({ loading: true, error: "", errorCode: "" });
    try {
      const response = await authApi.requestReactivation(payload);
      set({ loading: false });
      useUiStore.getState().notify({
        tone: "info",
        title: "Reactivation requested",
        message: response?.detail || "Support will review the account reactivation request.",
        icon: "support_agent"
      });
      return response;
    } catch (error) {
      set({ error: messageFromError(error) || "Could not request account reactivation.", errorCode: error?.normalized?.code || "", loading: false });
      throw error;
    }
  },

  updateProfile: async (payload) => {
    set({ loading: true, error: "", errorCode: "" });
    try {
      const previousEmail = get().user?.email || "";
      const response = await authApi.updateProfile(payload);
      const nextUser = response?.user || null;
      set({ user: nextUser, loading: false, initialized: true });
      const emailChanged = Boolean(previousEmail && nextUser?.email && previousEmail !== nextUser.email);
      useUiStore.getState().notify({
        title: "Profile saved",
        message: emailChanged ? "Check your inbox to verify the new email address." : "Your account details were updated.",
        icon: emailChanged ? "outgoing_mail" : "manage_accounts"
      });
      return nextUser;
    } catch (error) {
      set({ error: messageFromError(error) || "Profile update failed.", errorCode: error?.normalized?.code || "", loading: false });
      throw error;
    }
  },

  changePassword: async (payload) => {
    set({ loading: true, error: "", errorCode: "" });
    try {
      const response = await authApi.changePassword(payload);
      set({ loading: false, error: "" });
      useUiStore.getState().notify({ title: "Password changed", message: "Your password was updated.", icon: "lock_reset" });
      return response;
    } catch (error) {
      set({ error: messageFromError(error) || "Password change failed.", errorCode: error?.normalized?.code || "", loading: false });
      throw error;
    }
  },

  verifyLoginTwoFactor: async (payload) => {
    set({ loading: true, error: "", errorCode: "" });
    try {
      const response = await authApi.loginTwoFactor(payload);
      set({ user: response?.user || null, pendingTwoFactor: null, initialized: true, loading: false });
      useUiStore.getState().notify({ title: "Signed in", message: "Welcome back.", icon: "login" });
      return response;
    } catch (error) {
      set({ error: messageFromError(error) || "Invalid verification code.", errorCode: error?.normalized?.code || "", loading: false });
      throw error;
    }
  },

  verifyEmail: async (payload) => {
    set({ loading: true, error: "", errorCode: "" });
    try {
      const response = await authApi.verifyEmail(payload);
      const currentUser = get().user;
      const verifiedUser = response?.user || null;
      const shouldRefreshCurrentUser = currentUser && (!verifiedUser || verifiedUser.id === currentUser.id);
      set({
        user: shouldRefreshCurrentUser ? verifiedUser || currentUser : currentUser,
        loading: false,
        initialized: true
      });
      useUiStore.getState().notify({ title: "Email verified", message: "Your account email is confirmed.", icon: "mark_email_read" });
      return response;
    } catch (error) {
      set({ error: messageFromError(error) || "Email verification failed.", errorCode: error?.normalized?.code || "", loading: false });
      throw error;
    }
  },

  resendEmailVerification: async () => {
    set({ loading: true, error: "", errorCode: "" });
    try {
      const response = await authApi.resendEmailVerification();
      set({ user: response?.user || get().user, loading: false, initialized: true });
      useUiStore.getState().notify({ title: "Verification sent", message: "Check your inbox for the new link.", icon: "outgoing_mail" });
      return response;
    } catch (error) {
      set({ error: messageFromError(error) || "Could not send verification email.", errorCode: error?.normalized?.code || "", loading: false });
      throw error;
    }
  },

  logout: async () => {
    set({ loading: true, error: "", errorCode: "" });
    try {
      await authApi.logout();
    } catch {
      // Local session state should still clear if the server session is already gone.
    }
    set({ user: null, pendingTwoFactor: null, initialized: true, loading: false, error: "", errorCode: "" });
    useUiStore.getState().notify({ tone: "info", title: "Signed out", message: "You have been signed out.", icon: "logout" });
  },

  clearError: () => set({ error: "", errorCode: "" }),
  clearPendingTwoFactor: () => set({ pendingTwoFactor: null, error: "", errorCode: "" }),
  isAuthenticated: () => Boolean(get().user)
}));
