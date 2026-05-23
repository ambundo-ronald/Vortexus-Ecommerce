import apiClient from "./axiosClient";
import { ENDPOINTS } from "../constants/apiEndpoints";

export const analyticsApi = {
  track: (payload) => apiClient.post(ENDPOINTS.analytics.events, payload).then((response) => response.data)
};
