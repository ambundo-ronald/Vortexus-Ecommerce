import apiClient from "./axiosClient";
import { ENDPOINTS } from "../constants/apiEndpoints";

export const checkoutApi = {
  basket: () => apiClient.get(ENDPOINTS.checkout.basket).then((response) => response.data),
  addItem: (payload) => apiClient.post(ENDPOINTS.checkout.basketItems, payload).then((response) => response.data),
  updateLine: (lineId, payload) =>
    apiClient.patch(ENDPOINTS.checkout.basketLine(lineId), payload).then((response) => response.data),
  removeLine: (lineId) => apiClient.delete(ENDPOINTS.checkout.basketLine(lineId)).then((response) => response.data),
  shipping: () => apiClient.get(ENDPOINTS.checkout.shipping).then((response) => response.data),
  addresses: () => apiClient.get(ENDPOINTS.checkout.addresses).then((response) => response.data),
  saveShippingAddress: (payload) =>
    apiClient.put(ENDPOINTS.checkout.shippingAddress, payload).then((response) => response.data),
  useShippingAddress: (payload) =>
    apiClient.post(ENDPOINTS.checkout.useShippingAddress, payload).then((response) => response.data),
  selectShippingMethod: (payload) =>
    apiClient.post(ENDPOINTS.checkout.shippingSelect, payload).then((response) => response.data),
  billing: () => apiClient.get(ENDPOINTS.checkout.billing).then((response) => response.data),
  saveBillingAddress: (payload) =>
    apiClient.put(ENDPOINTS.checkout.billingAddress, payload).then((response) => response.data),
  useBillingAddress: (payload) =>
    apiClient.post(ENDPOINTS.checkout.useBillingAddress, payload).then((response) => response.data),
  preview: () => apiClient.get(ENDPOINTS.checkout.preview).then((response) => response.data),
  placeOrder: (payload) => apiClient.post(ENDPOINTS.checkout.orders, payload).then((response) => response.data),
  thankYou: (orderNumber) =>
    apiClient.get(ENDPOINTS.checkout.thankYou, { params: orderNumber ? { order_number: orderNumber } : undefined }).then((response) => response.data),
  savedItems: () => apiClient.get(ENDPOINTS.checkout.saved).then((response) => response.data),
  saveForLater: (lineId) => apiClient.post(ENDPOINTS.checkout.saveForLater(lineId)).then((response) => response.data),
  moveSavedToCart: (savedLineId) => apiClient.post(ENDPOINTS.checkout.moveSavedToCart(savedLineId)).then((response) => response.data),
  removeSavedItem: (savedLineId) => apiClient.delete(ENDPOINTS.checkout.savedItem(savedLineId)).then((response) => response.data),
  applyVoucher: (payload) => apiClient.post(ENDPOINTS.checkout.vouchers, payload).then((response) => response.data),
  removeVoucher: (voucherId) => apiClient.delete(ENDPOINTS.checkout.voucher(voucherId)).then((response) => response.data)
};
