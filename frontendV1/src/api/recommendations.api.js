import apiClient from "./axiosClient";
import { ENDPOINTS } from "../constants/apiEndpoints";

export const recommendationsApi = {
  list: (params) => apiClient.get(ENDPOINTS.recommendations, { params }).then((response) => response.data)
};
