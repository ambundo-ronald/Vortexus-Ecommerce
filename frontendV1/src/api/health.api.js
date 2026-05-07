import apiClient from "./axiosClient";
import { ENDPOINTS } from "../constants/apiEndpoints";

export const healthApi = {
  live: () => apiClient.get(ENDPOINTS.health.live).then((response) => response.data),
  ready: () => apiClient.get(ENDPOINTS.health.ready).then((response) => response.data)
};
