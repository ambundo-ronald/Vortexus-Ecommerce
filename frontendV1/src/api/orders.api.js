import apiClient from "./axiosClient";
import { ENDPOINTS } from "../constants/apiEndpoints";

export const ordersApi = {
  list: (params) => apiClient.get(ENDPOINTS.orders.account, { params }).then((response) => response.data),
  detail: (orderNumber) => apiClient.get(ENDPOINTS.orders.detail(orderNumber)).then((response) => response.data),
  status: (orderNumber) => apiClient.get(ENDPOINTS.orders.status(orderNumber)).then((response) => response.data),
  reorder: (orderNumber) => apiClient.post(ENDPOINTS.orders.reorder(orderNumber)).then((response) => response.data)
};
