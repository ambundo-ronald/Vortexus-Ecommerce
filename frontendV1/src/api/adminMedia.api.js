import apiClient from "./axiosClient";
import { ENDPOINTS } from "../constants/apiEndpoints";

export const adminMediaApi = {
  list: (params) => apiClient.get(ENDPOINTS.admin.media, { params }).then((response) => response.data),
  detail: (imageId) => apiClient.get(ENDPOINTS.admin.mediaItem(imageId)).then((response) => response.data),
  remove: (imageId) => apiClient.delete(ENDPOINTS.admin.mediaItem(imageId)).then((response) => response.data)
};
