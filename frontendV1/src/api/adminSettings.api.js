import apiClient from "./axiosClient";
import { ENDPOINTS } from "../constants/apiEndpoints";

export const adminSettingsApi = {
  get: () => apiClient.get(ENDPOINTS.admin.settings).then((response) => response.data),
  update: (payload) => apiClient.patch(ENDPOINTS.admin.settings, payload).then((response) => response.data)
};
