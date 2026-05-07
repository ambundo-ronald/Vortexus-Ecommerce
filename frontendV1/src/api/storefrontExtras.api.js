import apiClient from "./axiosClient";
import { ENDPOINTS } from "../constants/apiEndpoints";

export const storefrontExtrasApi = {
  vouchers: {
    apply: (payload) => apiClient.post(ENDPOINTS.checkout.vouchers, payload).then((response) => response.data),
    remove: (voucherId) => apiClient.delete(ENDPOINTS.checkout.voucher(voucherId)).then((response) => response.data)
  },
  offers: {
    list: (params) => apiClient.get(ENDPOINTS.offers.list, { params }).then((response) => response.data),
    detail: (slug) => apiClient.get(ENDPOINTS.offers.detail(slug)).then((response) => response.data),
    range: (slug, params) => apiClient.get(ENDPOINTS.catalog.range(slug), { params }).then((response) => response.data)
  },
  savedItems: {
    list: () => apiClient.get(ENDPOINTS.checkout.saved).then((response) => response.data),
    saveForLater: (lineId) =>
      apiClient.post(ENDPOINTS.checkout.saveForLater(lineId)).then((response) => response.data),
    moveToCart: (savedLineId) =>
      apiClient.post(ENDPOINTS.checkout.moveSavedToCart(savedLineId)).then((response) => response.data),
    remove: (savedLineId) => apiClient.delete(ENDPOINTS.checkout.savedItem(savedLineId)).then((response) => response.data)
  },
  addresses: {
    list: () => apiClient.get(ENDPOINTS.account.addresses).then((response) => response.data),
    create: (payload) => apiClient.post(ENDPOINTS.account.addresses, payload).then((response) => response.data),
    detail: (addressId) => apiClient.get(ENDPOINTS.account.address(addressId)).then((response) => response.data),
    update: (addressId, payload) =>
      apiClient.patch(ENDPOINTS.account.address(addressId), payload).then((response) => response.data),
    remove: (addressId) => apiClient.delete(ENDPOINTS.account.address(addressId)).then((response) => response.data),
    setDefaultShipping: (addressId) =>
      apiClient.post(ENDPOINTS.account.defaultShippingAddress(addressId)).then((response) => response.data),
    setDefaultBilling: (addressId) =>
      apiClient.post(ENDPOINTS.account.defaultBillingAddress(addressId)).then((response) => response.data),
    checkout: () => apiClient.get(ENDPOINTS.checkout.addresses).then((response) => response.data),
    useShipping: (payload) => apiClient.post(ENDPOINTS.checkout.useShippingAddress, payload).then((response) => response.data),
    useBilling: (payload) => apiClient.post(ENDPOINTS.checkout.useBillingAddress, payload).then((response) => response.data)
  },
  billing: {
    get: () => apiClient.get(ENDPOINTS.checkout.billing).then((response) => response.data),
    saveAddress: (payload) => apiClient.put(ENDPOINTS.checkout.billingAddress, payload).then((response) => response.data)
  },
  orders: {
    guestLookup: (payload) => apiClient.post(ENDPOINTS.orders.guestLookup, payload).then((response) => response.data),
    guestDetail: (orderNumber, hash) =>
      apiClient.get(ENDPOINTS.orders.guestDetail(orderNumber, hash)).then((response) => response.data),
    line: (orderNumber, lineId) => apiClient.get(ENDPOINTS.orders.line(orderNumber, lineId)).then((response) => response.data)
  },
  messages: {
    emails: () => apiClient.get(ENDPOINTS.account.emails).then((response) => response.data),
    email: (emailId) => apiClient.get(ENDPOINTS.account.email(emailId)).then((response) => response.data),
    notifications: () => apiClient.get(ENDPOINTS.account.notifications).then((response) => response.data),
    archivedNotifications: () => apiClient.get(ENDPOINTS.account.notificationArchive).then((response) => response.data),
    notification: (notificationId) =>
      apiClient.get(ENDPOINTS.account.notification(notificationId)).then((response) => response.data),
    markRead: (notificationId) =>
      apiClient.post(ENDPOINTS.account.notificationRead(notificationId)).then((response) => response.data),
    archive: (notificationId) =>
      apiClient.post(ENDPOINTS.account.notificationArchiveAction(notificationId)).then((response) => response.data),
    readAll: () => apiClient.post(ENDPOINTS.account.notificationsReadAll).then((response) => response.data)
  },
  productAlerts: {
    list: () => apiClient.get(ENDPOINTS.account.productAlerts).then((response) => response.data),
    create: (productId, payload) =>
      apiClient.post(ENDPOINTS.catalog.productAlerts(productId), payload).then((response) => response.data),
    confirm: (key) => apiClient.post(ENDPOINTS.productAlerts.confirm(key)).then((response) => response.data),
    cancel: (key) => apiClient.post(ENDPOINTS.productAlerts.cancel(key)).then((response) => response.data),
    remove: (alertId) => apiClient.delete(ENDPOINTS.account.productAlert(alertId)).then((response) => response.data)
  },
  account: {
    passwordResetRequest: (payload) =>
      apiClient.post(ENDPOINTS.account.passwordResetRequest, payload).then((response) => response.data),
    passwordResetConfirm: (payload) =>
      apiClient.post(ENDPOINTS.account.passwordResetConfirm, payload).then((response) => response.data),
    delete: (payload) => apiClient.post(ENDPOINTS.account.delete, payload).then((response) => response.data),
    preferences: () => apiClient.get(ENDPOINTS.account.preferences).then((response) => response.data),
    updatePreferences: (payload) =>
      apiClient.patch(ENDPOINTS.account.preferences, payload).then((response) => response.data),
    recentlyViewed: () => apiClient.get(ENDPOINTS.account.recentlyViewed).then((response) => response.data),
    markViewed: (productId) => apiClient.post(ENDPOINTS.catalog.productViewed(productId)).then((response) => response.data)
  },
  reviews: {
    detail: (productId, reviewId) =>
      apiClient.get(ENDPOINTS.catalog.productReview(productId, reviewId)).then((response) => response.data)
  },
  search: {
    facets: (params) => apiClient.get(ENDPOINTS.search.facets, { params }).then((response) => response.data)
  },
  wishlist: {
    moveItem: (wishlistId, productId, payload) =>
      apiClient.post(ENDPOINTS.wishlist.moveItem(wishlistId, productId), payload).then((response) => response.data),
    shared: (key) => apiClient.get(ENDPOINTS.wishlist.shared(key)).then((response) => response.data)
  }
};
