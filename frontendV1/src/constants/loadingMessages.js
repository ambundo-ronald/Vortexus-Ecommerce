const loadingMessageGroups = {
  account: [
    "Checking your account securely",
    "Loading your saved details",
    "Preparing your account"
  ],
  cart: [
    "Opening your cart",
    "Checking stock and current prices",
    "Preparing your order summary"
  ],
  checkout: [
    "Preparing secure checkout",
    "Checking delivery and order details",
    "Getting the next step ready"
  ],
  email: [
    "Checking your secure link",
    "Confirming your email details",
    "Finishing verification"
  ],
  orders: [
    "Retrieving your order",
    "Checking its latest status",
    "Preparing the order details"
  ],
  products: [
    "Finding the right products",
    "Checking prices and availability",
    "Preparing your results"
  ],
  reviews: [
    "Gathering customer feedback",
    "Checking the latest reviews",
    "Preparing the review details"
  ],
  supplier: [
    "Connecting to your supplier workspace",
    "Loading products and orders",
    "Preparing your workspace"
  ],
  default: [
    "Connecting securely",
    "Loading the latest information",
    "Almost ready"
  ]
};

export function loadingMessagesFor(label = "") {
  const normalized = String(label).toLowerCase();

  if (matches(normalized, ["payment", "checkout", "shipping", "order preview"])) {
    return loadingMessageGroups.checkout;
  }
  if (matches(normalized, ["cart", "saved item", "basket"])) {
    return loadingMessageGroups.cart;
  }
  if (matches(normalized, ["supplier"])) {
    return loadingMessageGroups.supplier;
  }
  if (matches(normalized, ["verify", "verification", "secure link"])) {
    return loadingMessageGroups.email;
  }
  if (matches(normalized, ["review"])) {
    return loadingMessageGroups.reviews;
  }
  if (matches(normalized, ["order", "track"])) {
    return loadingMessageGroups.orders;
  }
  if (matches(normalized, ["account", "profile", "preference", "address", "wishlist", "notification", "message"])) {
    return loadingMessageGroups.account;
  }
  if (matches(normalized, ["product", "offer", "range", "catalog", "search", "recommendation"])) {
    return loadingMessageGroups.products;
  }

  return loadingMessageGroups.default;
}

function matches(value, terms) {
  return terms.some((term) => value.includes(term));
}

