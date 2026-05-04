import apiClient from "./axiosClient";
import { ENDPOINTS } from "../constants/apiEndpoints";

export const checkoutApi = {
  basket: () => apiClient.get(ENDPOINTS.checkout.basket).then((response) => response.data),
  addItem: (payload) => apiClient.post(ENDPOINTS.checkout.basketItems, payload).then((response) => response.data),
  updateLine: (lineId, payload) =>
    apiClient.patch(ENDPOINTS.checkout.basketLine(lineId), payload).then((response) => response.data),
  removeLine: (lineId) => apiClient.delete(ENDPOINTS.checkout.basketLine(lineId)).then((response) => response.data),
  shipping: () => apiClient.get(ENDPOINTS.checkout.shipping).then((response) => response.data),
  saveShippingAddress: (payload) =>
    apiClient.put(ENDPOINTS.checkout.shippingAddress, payload).then((response) => response.data),
  selectShippingMethod: (payload) =>
    apiClient.post(ENDPOINTS.checkout.shippingSelect, payload).then((response) => response.data),
  placeOrder: (payload) => apiClient.post(ENDPOINTS.checkout.orders, payload).then((response) => response.data)
};
