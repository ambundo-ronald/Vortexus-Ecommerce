import apiClient from "./axiosClient";
import { ENDPOINTS } from "../constants/apiEndpoints";

export const searchApi = {
  text: (params) => apiClient.get(ENDPOINTS.search.text, { params }).then((response) => response.data),
  suggestions: (params) => apiClient.get(ENDPOINTS.search.suggestions, { params }).then((response) => response.data),
  image: (formData) => apiClient.post(ENDPOINTS.search.image, formData).then((response) => response.data)
};
