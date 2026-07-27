import apiClient from "./axiosClient";
import { ENDPOINTS } from "../constants/apiEndpoints";

export const personalShopperApi = {
  lists: () => apiClient.get(ENDPOINTS.personalShopper.lists).then((response) => response.data),
  hub: (token) => apiClient.get(ENDPOINTS.personalShopper.hub(token)).then((response) => response.data),
  markAddedToCart: (token) => apiClient.post(ENDPOINTS.personalShopper.addedToCart(token)).then((response) => response.data)
};
