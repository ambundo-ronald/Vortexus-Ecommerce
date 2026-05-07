import apiClient from "./axiosClient";
import { ENDPOINTS } from "../constants/apiEndpoints";

export const adminUsersApi = {
  list: (params) => apiClient.get(ENDPOINTS.admin.users, { params }).then((response) => response.data),
  detail: (userId) => apiClient.get(ENDPOINTS.admin.user(userId)).then((response) => response.data),
  update: (userId, payload) => apiClient.patch(ENDPOINTS.admin.user(userId), payload).then((response) => response.data)
};
