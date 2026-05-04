import apiClient from "./axiosClient";
import { ENDPOINTS } from "../constants/apiEndpoints";

export const adminOrdersApi = {
  list: (params) => apiClient.get(ENDPOINTS.admin.orders, { params }).then((response) => response.data),
  detail: (orderId) => apiClient.get(ENDPOINTS.admin.order(orderId)).then((response) => response.data),
  updateStatus: (orderId, payload) =>
    apiClient.patch(ENDPOINTS.admin.orderStatus(orderId), payload).then((response) => response.data)
};
