export const API_PREFIX = import.meta.env.VITE_API_PREFIX || "/api/v1";

export const ENDPOINTS = {
  docs: {
    html: "/docs/",
    json: "/docs.json"
  },
  health: {
    live: "/health/live/",
    ready: "/health/ready/"
  },
  account: {
    csrf: "/account/csrf/",
    register: "/account/register/",
    login: "/account/login/",
    logout: "/account/logout/",
    me: "/account/me/",
    password: "/account/password/"
  },
  catalog: {
    categories: "/catalog/categories/",
    products: "/catalog/products/",
    product: (productId) => `/catalog/products/${productId}/`,
    productReviews: (productId) => `/catalog/products/${productId}/reviews/`
  },
  search: {
    text: "/search/",
    suggestions: "/search/suggestions/",
    image: "/search/image/"
  },
  recommendations: "/recommendations/",
  quotes: "/quotes/",
  wishlist: {
    default: "/account/wishlist/",
    defaultItems: "/account/wishlist/items/",
    defaultItem: (productId) => `/account/wishlist/items/${productId}/`,
    status: "/account/wishlist/status/",
    lists: "/account/wishlists/",
    list: (wishlistId) => `/account/wishlists/${wishlistId}/`,
    listItems: (wishlistId) => `/account/wishlists/${wishlistId}/items/`,
    listItem: (wishlistId, productId) => `/account/wishlists/${wishlistId}/items/${productId}/`
  },
  reviews: {
    account: "/account/reviews/",
    accountReview: (reviewId) => `/account/reviews/${reviewId}/`
  },
  checkout: {
    basket: "/checkout/basket/",
    basketItems: "/checkout/basket/items/",
    basketLine: (lineId) => `/checkout/basket/items/${lineId}/`,
    shipping: "/checkout/shipping/",
    shippingAddress: "/checkout/shipping/address/",
    shippingSelect: "/checkout/shipping/select/",
    orders: "/checkout/orders/"
  },
  payments: {
    methods: "/checkout/payments/methods/",
    sessions: "/checkout/payments/",
    session: (reference) => `/checkout/payments/${reference}/`,
    confirm: (reference) => `/checkout/payments/${reference}/confirm/`,
    mpesaInit: "/checkout/payments/mpesa/initiate/",
    mpesaStatus: (reference) => `/checkout/payments/mpesa/${reference}/status/`,
    airtelInit: "/checkout/payments/airtel-money/initiate/",
    airtelStatus: (reference) => `/checkout/payments/airtel-money/${reference}/status/`,
    cardInit: "/checkout/payments/cards/initiate/"
  },
  orders: {
    account: "/account/orders/",
    detail: (orderNumber) => `/account/orders/${orderNumber}/`,
    status: (orderNumber) => `/account/orders/${orderNumber}/status/`,
    reorder: (orderNumber) => `/account/orders/${orderNumber}/reorder/`
  },
  supplier: {
    profile: "/supplier/profile/",
    dashboard: "/supplier/dashboard/",
    orders: "/supplier/orders/",
    order: (orderNumber) => `/supplier/orders/${orderNumber}/`,
    lineStatus: (orderNumber, lineId) => `/supplier/orders/${orderNumber}/lines/${lineId}/status/`,
    products: "/supplier/products/",
    product: (productId) => `/supplier/products/${productId}/`
  },
  admin: {
    suppliers: "/admin/suppliers/",
    supplier: (supplierId) => `/admin/suppliers/${supplierId}/`,
    auditLogs: "/admin/audit-logs/",
    auditLog: (auditLogId) => `/admin/audit-logs/${auditLogId}/`,
    users: "/admin/users/",
    user: (userId) => `/admin/users/${userId}/`,
    media: "/admin/media/",
    mediaItem: (imageId) => `/admin/media/${imageId}/`,
    settings: "/admin/settings/",
    orders: "/admin/orders/",
    order: (orderId) => `/admin/orders/${orderId}/`,
    orderStatus: (orderId) => `/admin/orders/${orderId}/status/`,
    integrations: "/admin/integrations/",
    integration: (connectionId) => `/admin/integrations/${connectionId}/`,
    integrationLogs: (connectionId) => `/admin/integrations/${connectionId}/logs/`,
    erpnextTest: (connectionId) => `/admin/integrations/${connectionId}/erpnext/test/`,
    erpnextPreview: (connectionId) => `/admin/integrations/${connectionId}/erpnext/preview/`,
    erpnextImport: (connectionId) => `/admin/integrations/${connectionId}/erpnext/import/`,
    erpnextStockSync: (connectionId) => `/admin/integrations/${connectionId}/erpnext/stock-sync/`,
    products: "/admin/products/",
    product: (productId) => `/admin/products/${productId}/`,
    productImages: (productId) => `/admin/products/${productId}/images/`,
    productImage: (productId, imageId) => `/admin/products/${productId}/images/${imageId}/`
  }
};
