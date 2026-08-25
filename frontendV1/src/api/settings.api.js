import apiClient from "./axiosClient";
import { ENDPOINTS } from "../constants/apiEndpoints";

export const settingsApi = {
  public: () => apiClient.get(ENDPOINTS.content.settings).then((response) => response.data)
};
