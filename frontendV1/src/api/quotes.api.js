import apiClient from "./axiosClient";
import { ENDPOINTS } from "../constants/apiEndpoints";

export const quotesApi = {
  create: (payload) => apiClient.post(ENDPOINTS.quotes, payload).then((response) => response.data)
};
