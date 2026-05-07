import apiClient from "./axiosClient";
import { ENDPOINTS } from "../constants/apiEndpoints";

export const docsApi = {
  json: () => apiClient.get(ENDPOINTS.docs.json).then((response) => response.data)
};
