import apiClient from "./axiosClient";
import { ENDPOINTS } from "../constants/apiEndpoints";

export const contentApi = {
  marketingBlocks: (params) =>
    apiClient.get(ENDPOINTS.content.marketingBlocks, { params }).then((response) => response.data)
};
