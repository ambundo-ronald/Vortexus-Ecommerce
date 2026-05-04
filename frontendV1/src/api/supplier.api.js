import apiClient from "./axiosClient";
import { ENDPOINTS } from "../constants/apiEndpoints";

export const supplierApi = {
  profile: () => apiClient.get(ENDPOINTS.supplier.profile).then((response) => response.data),
  createProfile: (payload) => apiClient.post(ENDPOINTS.supplier.profile, payload).then((response) => response.data),
  updateProfile: (payload) => apiClient.patch(ENDPOINTS.supplier.profile, payload).then((response) => response.data),
  dashboard: () => apiClient.get(ENDPOINTS.supplier.dashboard).then((response) => response.data),
  orders: (params) => apiClient.get(ENDPOINTS.supplier.orders, { params }).then((response) => response.data),
  order: (orderNumber) => apiClient.get(ENDPOINTS.supplier.order(orderNumber)).then((response) => response.data),
  updateOrderLineStatus: (orderNumber, lineId, payload) =>
    apiClient.post(ENDPOINTS.supplier.lineStatus(orderNumber, lineId), payload).then((response) => response.data),
  products: (params) => apiClient.get(ENDPOINTS.supplier.products, { params }).then((response) => response.data),
  createProduct: (payload) => apiClient.post(ENDPOINTS.supplier.products, payload).then((response) => response.data),
  product: (productId) => apiClient.get(ENDPOINTS.supplier.product(productId)).then((response) => response.data),
  updateProduct: (productId, payload) =>
    apiClient.patch(ENDPOINTS.supplier.product(productId), payload).then((response) => response.data),
  removeProduct: (productId) => apiClient.delete(ENDPOINTS.supplier.product(productId)).then((response) => response.data)
};
