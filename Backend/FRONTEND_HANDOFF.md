# Frontend Handoff

This document is for the frontend developer integrating with the Vortexus backend MVP.

Backend base URL in local development:

```text
http://127.0.0.1:8000
```

API base URL:

```text
http://127.0.0.1:8000/api/v1
```

## 1) Integration Model

- Authentication is session-based.
- CSRF protection is enabled for all mutating requests.
- Currency display is resolved by backend logic based on user profile / country / checkout context.
- Order, supplier, wishlist, review, and checkout logic already lives in the backend.
- Frontend should treat the backend as the source of truth for:
  - availability
  - pricing
  - tax
  - shipping options
  - payment state
  - order state

## 2) Required Auth Flow

Before any `POST`, `PUT`, `PATCH`, or `DELETE` request:

1. Call:
   - `GET /api/v1/account/csrf/`
2. Store:
   - session cookies
   - `csrf_token` from response JSON
3. Send for all mutating requests:
   - cookies with credentials
   - header `X-CSRFToken: <csrf_token>`

Example response:

```json
{
  "csrf_token": "..."
}
```

## 3) Standard Error Contract

All API errors follow this shape:

```json
{
  "error": {
    "code": "validation_error",
    "detail": "Request validation failed.",
    "status": 400,
    "errors": {
      "field": ["message"]
    }
  }
}
```

Throttled responses also include:

```json
{
  "error": {
    "code": "throttled",
    "detail": "Request was throttled. Expected available in 3600 seconds.",
    "status": 429,
    "retry_after_seconds": 3600
  }
}
```

## 4) Useful Local Accounts

Bootstrap command:

```powershell
python manage.py bootstrap_demo_data --with-order --with-reviews --with-wishlist
```

Seeded accounts:

- Admin:
  - email: `admin@vortexus.demo`
  - username: `admin_demo`
  - password: `Adminpass123!`
- Customer:
  - email: `customer@vortexus.demo`
  - username: `customer_demo`
  - password: `Customerpass123!`
- Supplier Alpha:
  - email: `supplier.alpha@vortexus.demo`
  - username: `supplier_alpha`
  - password: `Supplierpass123!`
- Supplier Beta:
  - email: `supplier.beta@vortexus.demo`
  - username: `supplier_beta`
  - password: `Supplierpass123!`

## 5) Core API Groups

### Public / Catalog

- `GET /api/v1/health/live/`
- `GET /api/v1/health/ready/`
- `GET /api/v1/docs/`
- `GET /api/v1/docs.json`
- `GET /api/v1/catalog/categories/`
- `GET /api/v1/catalog/products/`
- `GET /api/v1/catalog/products/<product_id>/`
- `GET /api/v1/search/?q=...`
- `POST /api/v1/search/image/`
- `GET /api/v1/recommendations/?limit=...`
- `GET /api/v1/catalog/products/<product_id>/reviews/`
- `POST /api/v1/quotes/`

### Account

- `GET /api/v1/account/csrf/`
- `POST /api/v1/account/register/`
- `POST /api/v1/account/login/`
- `POST /api/v1/account/logout/`
- `GET /api/v1/account/me/`
- `PATCH /api/v1/account/me/`
- `POST /api/v1/account/password/`

### Wishlist

- `GET /api/v1/account/wishlist/`
- `POST /api/v1/account/wishlist/items/`
- `DELETE /api/v1/account/wishlist/items/<product_id>/`
- `POST /api/v1/account/wishlist/status/`
- `GET /api/v1/account/wishlists/`
- `POST /api/v1/account/wishlists/`

### Reviews

- `GET /api/v1/catalog/products/<product_id>/reviews/`
- `POST /api/v1/catalog/products/<product_id>/reviews/`
- `GET /api/v1/account/reviews/`
- `GET /api/v1/account/reviews/<review_id>/`
- `PATCH /api/v1/account/reviews/<review_id>/`
- `DELETE /api/v1/account/reviews/<review_id>/`

### Checkout

- `GET /api/v1/checkout/basket/`
- `POST /api/v1/checkout/basket/items/`
- `PATCH /api/v1/checkout/basket/items/<line_id>/`
- `DELETE /api/v1/checkout/basket/items/<line_id>/`
- `GET /api/v1/checkout/shipping/`
- `PUT /api/v1/checkout/shipping/address/`
- `POST /api/v1/checkout/shipping/select/`

### Payments

- `GET /api/v1/checkout/payments/methods/`
- `POST /api/v1/checkout/payments/`
- `GET /api/v1/checkout/payments/<reference>/`
- `POST /api/v1/checkout/payments/<reference>/confirm/`

Provider-specific:

- `POST /api/v1/checkout/payments/mpesa/initiate/`
- `GET /api/v1/checkout/payments/mpesa/<reference>/status/`
- `POST /api/v1/payments/mpesa/callback/`
- `POST /api/v1/checkout/payments/airtel-money/initiate/`
- `GET /api/v1/checkout/payments/airtel-money/<reference>/status/`
- `POST /api/v1/payments/airtel-money/callback/`
- `POST /api/v1/checkout/payments/cards/initiate/`

### Orders

- `POST /api/v1/checkout/orders/`
- `GET /api/v1/account/orders/`
- `GET /api/v1/account/orders/<order_number>/`
- `GET /api/v1/account/orders/<order_number>/status/`
- `POST /api/v1/account/orders/<order_number>/reorder/`

### Supplier

- `GET /api/v1/supplier/profile/`
- `POST /api/v1/supplier/profile/`
- `PATCH /api/v1/supplier/profile/`
- `GET /api/v1/supplier/dashboard/`
- `GET /api/v1/supplier/orders/`
- `GET /api/v1/supplier/orders/<order_number>/`
- `POST /api/v1/supplier/orders/<order_number>/lines/<line_id>/status/`
- `GET /api/v1/supplier/products/`
- `POST /api/v1/supplier/products/`
- `GET /api/v1/supplier/products/<id>/`
- `PATCH /api/v1/supplier/products/<id>/`
- `DELETE /api/v1/supplier/products/<id>/`

### Admin / Staff

- `GET /api/v1/admin/suppliers/`
- `PATCH /api/v1/admin/suppliers/<id>/`
- `GET /api/v1/admin/audit-logs/`
- `GET /api/v1/admin/audit-logs/<id>/`

## 6) Frontend Sequence: Product Discovery

Recommended page load sequence:

1. `GET /api/v1/catalog/categories/`
2. `GET /api/v1/catalog/products/?page=1&page_size=24`
3. Optional:
   - `GET /api/v1/recommendations/?limit=8`
   - `GET /api/v1/search/?q=pump`

Notes:

- `catalog/products` is the main PLP data source.
- Search is a dedicated query endpoint.
- Product detail should use:
  - `GET /api/v1/catalog/products/<product_id>/`
- Product detail review section should use:
  - `GET /api/v1/catalog/products/<product_id>/reviews/`

## 7) Frontend Sequence: Authenticated Customer

Login:

1. `GET /api/v1/account/csrf/`
2. `POST /api/v1/account/login/`

Body:

```json
{
  "identifier": "customer_demo",
  "password": "Customerpass123!"
}
```

After login:

1. `GET /api/v1/account/me/`
2. `GET /api/v1/account/wishlist/`
3. `GET /api/v1/account/orders/`

## 8) Frontend Sequence: Checkout

Recommended order:

1. Add basket item
   - `POST /api/v1/checkout/basket/items/`
2. Read basket
   - `GET /api/v1/checkout/basket/`
3. Save shipping address
   - `PUT /api/v1/checkout/shipping/address/`
4. Read shipping options
   - `GET /api/v1/checkout/shipping/`
5. Select shipping method
   - `POST /api/v1/checkout/shipping/select/`
6. Initialize payment
7. Place order
   - `POST /api/v1/checkout/orders/`

Example shipping address payload:

```json
{
  "first_name": "Demo",
  "last_name": "Buyer",
  "line1": "Westlands Road",
  "line4": "Nairobi",
  "state": "Nairobi",
  "postcode": "00100",
  "country_code": "KE",
  "phone_number": "+254700000001"
}
```

Example shipping method payload:

```json
{
  "method_code": "dispatch-hub-pickup"
}
```

Example order placement payload:

```json
{
  "payment_reference": "PAY-ABC123DEF456"
}
```

## 9) Payment Notes By Method

### Cash on delivery

- Endpoint:
  - `POST /api/v1/checkout/payments/`
- Example:

```json
{
  "method": "cash_on_delivery"
}
```

- Current state:
  - working
  - suitable for immediate frontend integration

### Credit / debit card

- Endpoint:
  - `POST /api/v1/checkout/payments/cards/initiate/`
- Current backend behavior:
  - sandbox-style tokenized flow
  - no raw card storage
  - working for integration/testing

Example:

```json
{
  "method": "credit_card",
  "payer_email": "buyer@example.com",
  "payment_token": "tok_test_visa",
  "card_brand": "visa",
  "last4": "4242",
  "expiry_month": 12,
  "expiry_year": 2030,
  "holder_name": "Card Buyer"
}
```

### Airtel Money

- Endpoint:
  - `POST /api/v1/checkout/payments/airtel-money/initiate/`
- Current backend behavior:
  - sandbox-style pending collection
  - working for integration/testing

### M-Pesa

- Endpoint:
  - `POST /api/v1/checkout/payments/mpesa/initiate/`
- Current backend behavior:
  - route is implemented
  - returns `503 mpesa_not_configured` until Daraja sandbox credentials are added

This is expected right now.

## 10) Currency And Pricing

- The backend can return display prices in the user’s resolved currency.
- Base order/payment storage still uses backend order totals consistently.
- Frontend should display:
  - `price`
  - `currency`
- If present, frontend may also show:
  - `base_price`
  - `base_currency`

Do not recalculate prices client-side.

## 11) Basket And Availability Notes

Basket lines include:

- `reserved_quantity`
- `available_quantity`
- `availability`

Frontend should trust these values and not derive inventory state manually.

## 12) Supplier UI Notes

Supplier users should only be shown:

- supplier profile
- supplier dashboard
- supplier orders
- supplier-owned products

Supplier order detail is already filtered server-side to that supplier’s visible scope.

## 13) Admin UI Notes

Admin/staff-facing frontend areas can rely on:

- supplier approval list
- audit log list/detail

Catalog write APIs also exist for staff users.

## 14) Known Local Caveats

### OpenSearch not running locally

Current local state:

- OpenSearch is offline on `127.0.0.1:9200`
- readiness endpoint may report `degraded`
- backend still works
- text search falls back to DB-backed behavior
- indexing warnings may appear in the terminal

This does not block general frontend integration.

### M-Pesa sandbox not configured yet

Current local state:

- M-Pesa endpoints exist
- they return `503 mpesa_not_configured` until credentials are added

### Local email backend

Current local state:

- email goes to console output in development
- order confirmation and similar flows still execute

## 15) Verified Working Smoke Tests

The following have been smoke-tested successfully:

- public catalog/search/docs/health APIs
- customer login/profile/orders/wishlist/reviews
- supplier login/profile/dashboard/orders/products
- admin login/suppliers/audit logs
- checkout basket flow
- save shipping address
- shipping method selection
- payment initialization:
  - `cash_on_delivery`
  - `credit_card`
  - `airtel_money`
- order placement with `cash_on_delivery`

## 16) Recommended Frontend Starting Point

If the frontend team wants the lowest-risk sequence, start in this order:

1. session + CSRF setup
2. public catalog pages
3. login/register/profile
4. wishlist
5. cart + shipping
6. cash on delivery checkout
7. order history/detail
8. card checkout
9. Airtel Money checkout
10. M-Pesa once sandbox credentials are wired

## 17) Documentation References

- Human-readable API docs:
  - `/api/v1/docs/`
- JSON contract:
  - `/api/v1/docs.json`
- Main backend setup notes:
  - [README.md](C:/Users/user/Desktop/vortexus/Backend/README.md)
