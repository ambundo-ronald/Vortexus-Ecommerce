import apiClient from "./axiosClient";
import { ENDPOINTS } from "../constants/apiEndpoints";

export const adminIntegrationsApi = {
  list: (params) => apiClient.get(ENDPOINTS.admin.integrations, { params }).then((response) => response.data),
  create: (payload) => apiClient.post(ENDPOINTS.admin.integrations, payload).then((response) => response.data),
  detail: (connectionId) => apiClient.get(ENDPOINTS.admin.integration(connectionId)).then((response) => response.data),
  update: (connectionId, payload) =>
    apiClient.patch(ENDPOINTS.admin.integration(connectionId), payload).then((response) => response.data),
  logs: (connectionId, params) =>
    apiClient.get(ENDPOINTS.admin.integrationLogs(connectionId), { params }).then((response) => response.data),
  testErpNext: (connectionId) =>
    apiClient.post(ENDPOINTS.admin.erpnextTest(connectionId)).then((response) => response.data),
  previewErpNext: (connectionId, params) =>
    apiClient.get(ENDPOINTS.admin.erpnextPreview(connectionId), { params }).then((response) => response.data),
  importErpNext: (connectionId, payload) =>
    apiClient.post(ENDPOINTS.admin.erpnextImport(connectionId), payload).then((response) => response.data),
  syncErpNextStock: (connectionId, payload) =>
    apiClient.post(ENDPOINTS.admin.erpnextStockSync(connectionId), payload).then((response) => response.data)
};
