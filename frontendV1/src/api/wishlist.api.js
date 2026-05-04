import apiClient from "./axiosClient";
import { ENDPOINTS } from "../constants/apiEndpoints";

export const wishlistApi = {
  defaultList: () => apiClient.get(ENDPOINTS.wishlist.default).then((response) => response.data),
  addDefaultItem: (payload) => apiClient.post(ENDPOINTS.wishlist.defaultItems, payload).then((response) => response.data),
  removeDefaultItem: (productId) =>
    apiClient.delete(ENDPOINTS.wishlist.defaultItem(productId)).then((response) => response.data),
  status: (payload) => apiClient.post(ENDPOINTS.wishlist.status, payload).then((response) => response.data),
  lists: () => apiClient.get(ENDPOINTS.wishlist.lists).then((response) => response.data),
  createList: (payload) => apiClient.post(ENDPOINTS.wishlist.lists, payload).then((response) => response.data),
  list: (wishlistId) => apiClient.get(ENDPOINTS.wishlist.list(wishlistId)).then((response) => response.data),
  addItem: (wishlistId, payload) =>
    apiClient.post(ENDPOINTS.wishlist.listItems(wishlistId), payload).then((response) => response.data),
  removeItem: (wishlistId, productId) =>
    apiClient.delete(ENDPOINTS.wishlist.listItem(wishlistId, productId)).then((response) => response.data)
};
