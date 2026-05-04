import apiClient from "./axiosClient";
import { ENDPOINTS } from "../constants/apiEndpoints";

export const reviewsApi = {
  productReviews: (productId, params) =>
    apiClient.get(ENDPOINTS.catalog.productReviews(productId), { params }).then((response) => response.data),
  createProductReview: (productId, payload) =>
    apiClient.post(ENDPOINTS.catalog.productReviews(productId), payload).then((response) => response.data),
  accountReviews: (params) => apiClient.get(ENDPOINTS.reviews.account, { params }).then((response) => response.data),
  accountReview: (reviewId) => apiClient.get(ENDPOINTS.reviews.accountReview(reviewId)).then((response) => response.data),
  updateAccountReview: (reviewId, payload) =>
    apiClient.patch(ENDPOINTS.reviews.accountReview(reviewId), payload).then((response) => response.data),
  removeAccountReview: (reviewId) =>
    apiClient.delete(ENDPOINTS.reviews.accountReview(reviewId)).then((response) => response.data)
};
