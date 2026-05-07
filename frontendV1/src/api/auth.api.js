import apiClient from "./axiosClient";
import { ENDPOINTS } from "../constants/apiEndpoints";

export const authApi = {
  csrf: () => apiClient.get(ENDPOINTS.account.csrf).then((response) => response.data),
  register: (payload) => apiClient.post(ENDPOINTS.account.register, payload).then((response) => response.data),
  login: (payload) => apiClient.post(ENDPOINTS.account.login, payload).then((response) => response.data),
  logout: () => apiClient.post(ENDPOINTS.account.logout).then((response) => response.data),
  me: () => apiClient.get(ENDPOINTS.account.me).then((response) => response.data),
  updateProfile: (payload) => apiClient.patch(ENDPOINTS.account.me, payload).then((response) => response.data),
  changePassword: (payload) => apiClient.post(ENDPOINTS.account.password, payload).then((response) => response.data)
};
