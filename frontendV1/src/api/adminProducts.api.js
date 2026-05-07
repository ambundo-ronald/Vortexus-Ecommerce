import apiClient from "./axiosClient";
import { ENDPOINTS } from "../constants/apiEndpoints";

export const adminProductsApi = {
  list: (params) => apiClient.get(ENDPOINTS.admin.products, { params }).then((response) => response.data),
  detail: (productId) => apiClient.get(ENDPOINTS.admin.product(productId)).then((response) => response.data),
  create: (payload) => apiClient.post(ENDPOINTS.admin.products, payload).then((response) => response.data),
  update: (productId, payload) => apiClient.patch(ENDPOINTS.admin.product(productId), payload).then((response) => response.data),
  remove: (productId) => apiClient.delete(ENDPOINTS.admin.product(productId)).then((response) => response.data),
  uploadImage: (productId, formData) =>
    apiClient.post(ENDPOINTS.admin.productImages(productId), formData).then((response) => response.data),
  removeImage: (productId, imageId) =>
    apiClient.delete(ENDPOINTS.admin.productImage(productId, imageId)).then((response) => response.data)
};
