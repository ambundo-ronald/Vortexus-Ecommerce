import axios from "axios";

import { API_PREFIX, ENDPOINTS } from "../constants/apiEndpoints";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

export const apiClient = axios.create({
  baseURL: `${API_BASE_URL}${API_PREFIX}`,
  withCredentials: true,
  headers: {
    Accept: "application/json"
  }
});

let csrfToken = "";

export function setCsrfToken(token) {
  csrfToken = token || "";
}

export async function ensureCsrfToken() {
  if (csrfToken) return csrfToken;
  const response = await apiClient.get(ENDPOINTS.account.csrf);
  csrfToken = response.data?.csrf_token || "";
  return csrfToken;
}

apiClient.interceptors.request.use(async (config) => {
  const method = String(config.method || "get").toUpperCase();
  if (!["GET", "HEAD", "OPTIONS"].includes(method)) {
    const token = await ensureCsrfToken();
    if (token) config.headers["X-CSRFToken"] = token;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => {
    if (response.data?.csrf_token) setCsrfToken(response.data.csrf_token);
    return response;
  },
  (error) => {
    const payload = error.response?.data;
    const detail = payload?.error?.detail || payload?.detail || error.message || "Request failed.";
    error.normalized = {
      message: detail,
      status: payload?.error?.status || error.response?.status,
      code: payload?.error?.code || "request_error",
      errors: payload?.error?.errors || null
    };
    return Promise.reject(error);
  }
);

export default apiClient;
