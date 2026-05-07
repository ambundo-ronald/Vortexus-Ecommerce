import apiClient from "./axiosClient";
import { ENDPOINTS } from "../constants/apiEndpoints";

export const paymentsApi = {
  methods: () => apiClient.get(ENDPOINTS.payments.methods).then((response) => response.data),
  initialize: (payload) => apiClient.post(ENDPOINTS.payments.sessions, payload).then((response) => response.data),
  detail: (reference) => apiClient.get(ENDPOINTS.payments.session(reference)).then((response) => response.data),
  confirm: (reference, payload) =>
    apiClient.post(ENDPOINTS.payments.confirm(reference), payload).then((response) => response.data),
  initializeMpesa: (payload) => apiClient.post(ENDPOINTS.payments.mpesaInit, payload).then((response) => response.data),
  mpesaStatus: (reference) => apiClient.get(ENDPOINTS.payments.mpesaStatus(reference)).then((response) => response.data),
  initializeAirtel: (payload) => apiClient.post(ENDPOINTS.payments.airtelInit, payload).then((response) => response.data),
  airtelStatus: (reference) => apiClient.get(ENDPOINTS.payments.airtelStatus(reference)).then((response) => response.data),
  initializeCard: (payload) => apiClient.post(ENDPOINTS.payments.cardInit, payload).then((response) => response.data)
};
