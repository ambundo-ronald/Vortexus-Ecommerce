import apiClient from "./axiosClient";
import { ENDPOINTS } from "../constants/apiEndpoints";

const crud = (collection, detail) => ({
  list: (params) => apiClient.get(collection, { params }).then((response) => response.data),
  create: (payload) => apiClient.post(collection, payload).then((response) => response.data),
  detail: (id) => apiClient.get(detail(id)).then((response) => response.data),
  update: (id, payload) => apiClient.patch(detail(id), payload).then((response) => response.data),
  remove: (id) => apiClient.delete(detail(id)).then((response) => response.data)
});

export const adminExtrasApi = {
  dashboardSummary: (params) => apiClient.get(ENDPOINTS.admin.dashboardSummary, { params }).then((response) => response.data),
  categories: {
    ...crud(ENDPOINTS.admin.catalogCategories, ENDPOINTS.admin.catalogCategory),
    createChild: (categoryId, payload) =>
      apiClient.post(ENDPOINTS.admin.catalogCategoryChildren(categoryId), payload).then((response) => response.data)
  },
  productTypes: crud(ENDPOINTS.admin.productTypes, ENDPOINTS.admin.productType),
  attributes: crud(ENDPOINTS.admin.attributes, ENDPOINTS.admin.attribute),
  options: crud(ENDPOINTS.admin.options, ENDPOINTS.admin.option),
  inventory: {
    stockAlerts: (params) => apiClient.get(ENDPOINTS.admin.stockAlerts, { params }).then((response) => response.data),
    updateStockAlert: (alertId, payload) =>
      apiClient.patch(ENDPOINTS.admin.stockAlert(alertId), payload).then((response) => response.data),
    lowStock: (params) => apiClient.get(ENDPOINTS.admin.lowStock, { params }).then((response) => response.data)
  },
  vouchers: {
    ...crud(ENDPOINTS.admin.vouchers, ENDPOINTS.admin.voucher),
    stats: (voucherId) => apiClient.get(ENDPOINTS.admin.voucherStats(voucherId)).then((response) => response.data)
  },
  offers: {
    ...crud(ENDPOINTS.admin.offers, ENDPOINTS.admin.offer),
    updateStatus: (offerId, payload) =>
      apiClient.patch(ENDPOINTS.admin.offerStatus(offerId), payload).then((response) => response.data)
  },
  ranges: {
    ...crud(ENDPOINTS.admin.ranges, ENDPOINTS.admin.range),
    products: (rangeId, params) =>
      apiClient.get(ENDPOINTS.admin.rangeProducts(rangeId), { params }).then((response) => response.data),
    addProduct: (rangeId, payload) =>
      apiClient.post(ENDPOINTS.admin.rangeProducts(rangeId), payload).then((response) => response.data),
    removeProduct: (rangeId, payload) =>
      apiClient.delete(ENDPOINTS.admin.rangeProducts(rangeId), { data: payload }).then((response) => response.data)
  },
  reviews: crud(ENDPOINTS.admin.reviews, ENDPOINTS.admin.review),
  orders: {
    statistics: (params) => apiClient.get(ENDPOINTS.admin.orderStatistics, { params }).then((response) => response.data),
    line: (orderNumber, lineId) =>
      apiClient.get(ENDPOINTS.admin.orderLine(orderNumber, lineId)).then((response) => response.data),
    updateShippingAddress: (orderNumber, payload) =>
      apiClient.patch(ENDPOINTS.admin.orderShippingAddress(orderNumber), payload).then((response) => response.data),
    addNote: (orderNumber, payload) =>
      apiClient.post(ENDPOINTS.admin.orderNotes(orderNumber), payload).then((response) => response.data)
  },
  partners: {
    ...crud(ENDPOINTS.admin.partners, ENDPOINTS.admin.partner),
    users: (partnerId) => apiClient.get(ENDPOINTS.admin.partnerUsers(partnerId)).then((response) => response.data),
    addUser: (partnerId, payload) =>
      apiClient.post(ENDPOINTS.admin.partnerUsers(partnerId), payload).then((response) => response.data),
    linkUser: (partnerId, userId) =>
      apiClient.post(ENDPOINTS.admin.partnerUserLink(partnerId, userId)).then((response) => response.data),
    unlinkUser: (partnerId, userId) =>
      apiClient.delete(ENDPOINTS.admin.partnerUserUnlink(partnerId, userId)).then((response) => response.data)
  },
  shipping: {
    ...crud(ENDPOINTS.admin.weightBasedShipping, ENDPOINTS.admin.weightBasedShippingMethod),
    addBand: (methodId, payload) =>
      apiClient.post(ENDPOINTS.admin.weightBasedShippingBands(methodId), payload).then((response) => response.data),
    updateBand: (methodId, bandId, payload) =>
      apiClient.patch(ENDPOINTS.admin.weightBasedShippingBand(methodId, bandId), payload).then((response) => response.data),
    removeBand: (methodId, bandId) =>
      apiClient.delete(ENDPOINTS.admin.weightBasedShippingBand(methodId, bandId)).then((response) => response.data)
  },
  pages: crud(ENDPOINTS.admin.pages, ENDPOINTS.admin.page),
  communications: {
    list: () => apiClient.get(ENDPOINTS.admin.communications).then((response) => response.data),
    detail: (slug) => apiClient.get(ENDPOINTS.admin.communication(slug)).then((response) => response.data),
    update: (slug, payload) => apiClient.patch(ENDPOINTS.admin.communication(slug), payload).then((response) => response.data)
  },
  reports: {
    list: () => apiClient.get(ENDPOINTS.admin.reports).then((response) => response.data),
    detail: (reportName, params) =>
      apiClient.get(ENDPOINTS.admin.report(reportName), { params }).then((response) => response.data)
  }
};
