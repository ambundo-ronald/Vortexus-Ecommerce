import apiClient from "./axiosClient";
import { ENDPOINTS } from "../constants/apiEndpoints";

export const catalogApi = {
  categories: () => apiClient.get(ENDPOINTS.catalog.categories).then((response) => response.data),
  products: (params) => apiClient.get(ENDPOINTS.catalog.products, { params }).then((response) => response.data),
  product: (productId) => apiClient.get(ENDPOINTS.catalog.product(productId)).then((response) => response.data)
};
