# Vortexus Backend (Django Oscar MVP)

This folder is backend-only. Frontend lives in `../Frontend`.

Backend scaffold for an industrial ecommerce MVP using Django Oscar with fast APIs for:
- text search
- image search
- product recommendations

## 1) Stack
- Django + Django Oscar
- PostgreSQL
- Redis (cache + Celery broker)
- OpenSearch (text + vector search)
- Celery (background jobs)
- CLIP embeddings (PyTorch + Hugging Face Transformers)

## 2) Project Structure
- `config/`: settings, URLs, ASGI/WSGI, Celery app
- `apps/search/`: text search API + indexing tasks
- `apps/image_search/`: image search API + CLIP embedding + indexing tasks
- `apps/recommendations/`: recommendation API + precompute tasks
- `apps/common/`: shared OpenSearch client and product serializer

## 3) Quick Start
1. Create and activate a virtual environment (Python 3.11 or 3.12 recommended).
2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
3. Copy environment template:
   ```powershell
   Copy-Item .env.example .env
   ```
4. Start infra services:
   ```powershell
   docker compose up -d
   ```
5. Run migrations and create admin user:
   ```powershell
   python manage.py migrate
   python manage.py createsuperuser
   ```
6. Create OpenSearch indices:
   ```powershell
   python manage.py bootstrap_search_indices
   ```
7. Backfill image embeddings:
   ```powershell
   python manage.py backfill_image_embeddings --sync
   ```
8. Run API server:
   ```powershell
   python manage.py runserver
   ```
9. Run Celery worker (new terminal):
   ```powershell
   celery -A config worker -l info
   ```

## 4) API Endpoints (MVP)
- `GET /api/v1/search/?q=compressor&page=1&page_size=24&in_stock=true`
- `POST /api/v1/search/image/` (multipart form with `image`, optional `category`, `top_k`)
- `GET /api/v1/recommendations/?product_id=123&limit=12`
- `GET /api/v1/recommendations/?user_id=77&limit=12`
- `GET /api/v1/recommendations/?limit=12` (trending fallback)
- `GET /api/v1/catalog/categories/`
- `GET /api/v1/catalog/products/?q=pump&category=borehole-pumps&in_stock=true&sort_by=price_asc&page=1&page_size=24`
- `GET /api/v1/catalog/products/<id>/`
- `POST /api/v1/quotes/` (name/email/phone/company/message + optional `product_id`)
- `GET /api/v1/account/orders/`
- `GET /api/v1/account/orders/<order_number>/`
- `GET /api/v1/account/orders/<order_number>/status/`
- `POST /api/v1/account/orders/<order_number>/reorder/`
- `GET /api/v1/checkout/payments/methods/`
- `POST /api/v1/checkout/payments/`
- `GET /api/v1/checkout/payments/<reference>/`
- `POST /api/v1/checkout/payments/<reference>/confirm/`
- `POST /api/v1/checkout/orders/` (places an order from the current basket + shipping session)
- `GET|POST|PATCH /api/v1/supplier/profile/`
- `GET /api/v1/supplier/dashboard/`
- `GET /api/v1/supplier/orders/`
- `GET /api/v1/supplier/orders/<order_number>/`
- `POST /api/v1/supplier/orders/<order_number>/lines/<line_id>/status/`
- `GET|POST /api/v1/supplier/products/`
- `GET|PATCH|DELETE /api/v1/supplier/products/<id>/`
- `GET /api/v1/admin/suppliers/`
- `PATCH /api/v1/admin/suppliers/<id>/`

## 5) Email Notifications
Implemented notification flows:
- account registration confirmation
- password change confirmation
- quote request acknowledgement to customer
- quote request alert to internal sales inbox
- reusable order confirmation email command
- reusable shipping update email command

Environment variables:
- `DEFAULT_FROM_EMAIL`
- `NOTIFICATION_REPLY_TO_EMAIL`
- `SALES_NOTIFICATION_RECIPIENTS`

Local development uses Django's console email backend by default, so emails print in the terminal.

Manual order/shipping email commands:

```powershell
python manage.py send_order_confirmation ORDER-10001
python manage.py send_shipping_update ORDER-10001 --status-label "Out for delivery" --tracking-reference TRK-10001
```

## 6) Supplier Marketplace Backend
Implemented marketplace flow:
- supplier application/profile creation linked to Oscar `Partner`
- supplier approval workflow (`pending`, `approved`, `suspended`)
- supplier dashboard metrics
- supplier order management
- marketplace order splitting by supplier
- supplier-owned product CRUD via supplier partner stock records
- safe supplier delete behavior:
  - removes only the supplier's own offer
  - deletes the product only if no supplier offers remain

Approval options:
- Django admin: `Supplier Profiles`
- API: `PATCH /api/v1/admin/suppliers/<id>/`

Supplier order endpoints:
- `GET /api/v1/supplier/orders/`
- `GET /api/v1/supplier/orders/<order_number>/`
- `POST /api/v1/supplier/orders/<order_number>/lines/<line_id>/status/`

Supplier order management behavior:
- suppliers only see orders containing their own lines
- supplier detail only exposes that supplier's lines
- supplier fulfillment updates create shipping events
- supplier shipping updates can roll up the order status
- shipped/delivered updates trigger customer shipping emails

Marketplace order splitting behavior:
- one customer checkout still creates one customer-facing order number
- backend creates supplier order groups under that order, one per supplier partner
- each supplier group carries its own:
  - status
  - line count
  - item count
  - subtotal share
  - shipping share
  - tracking reference
- customer order detail now exposes `supplier_groups`

## 7) Order Placement API
Implemented:
- validates basket readiness
- requires shipping address/method when shipping is needed
- supports guest checkout email capture
- requires a payment reference before order placement
- creates a real Oscar order
- submits the basket after successful placement
- sends order confirmation email

Endpoint:

```powershell
POST /api/v1/checkout/orders/
```

Example payload for guest checkout:

```json
{
  "guest_email": "buyer@example.com",
  "payment_reference": "PAY-ABC123DEF456"
}
```

## 8) Customer Order APIs
Implemented:
- authenticated order history listing
- authenticated order detail lookup
- lightweight order status tracking timeline
- reorder endpoint to add a previous order's items back into the active basket

Endpoints:
- `GET /api/v1/account/orders/`
- `GET /api/v1/account/orders/<order_number>/`
- `GET /api/v1/account/orders/<order_number>/status/`
- `POST /api/v1/account/orders/<order_number>/reorder/`

## 9) Payment API
Supported payment methods:
- `mpesa`
- `airtel_money`
- `credit_card`
- `debit_card`
- `bank_transfer`
- `cash_on_delivery`

Implemented:
- payment method discovery endpoint
- payment session initialization
- payment session status lookup
- payment confirmation endpoint for provider callback / backend testing
- payment linkage to Oscar payment `Source` and `Transaction` records on order placement

Important scope note:
- this is a gateway-ready backend contract
- live gateway credentials/webhooks are not wired yet
- `confirm` endpoint currently acts as the provider callback/testing hook for MVP development

### M-Pesa Daraja sandbox
Dedicated M-Pesa endpoints:
- `POST /api/v1/checkout/payments/mpesa/initiate/`
- `GET /api/v1/checkout/payments/mpesa/<reference>/status/`
- `POST /api/v1/payments/mpesa/callback/`

Required env vars:
- `MPESA_BASE_URL`
- `MPESA_CONSUMER_KEY`
- `MPESA_CONSUMER_SECRET`
- `MPESA_SHORTCODE`
- `MPESA_PASSKEY`
- `MPESA_CALLBACK_URL`
- `MPESA_TRANSACTION_TYPE`

Behavior:
- initiates STK push against Daraja sandbox when credentials are configured
- stores `MerchantRequestID` and `CheckoutRequestID` in the payment session
- updates payment session status from callback payloads
- allows order placement only after required payment completion

Example initialize payment payload:

```json
{
  "method": "mpesa",
  "payer_email": "buyer@example.com",
  "phone_number": "+254700000011"
}
```

### Card sandbox
Dedicated card endpoint:
- `POST /api/v1/checkout/payments/cards/initiate/`

Supported card methods:
- `credit_card`
- `debit_card`

Behavior:
- does not store raw PAN/card number
- accepts a sandbox payment token from the frontend/payment widget
- stores masked metadata such as `last4`, brand, expiry month/year, holder name
- authorizes the payment session for order placement

Required env vars:
- `CARD_SANDBOX_ENABLED`
- `CARD_PROVIDER_NAME`

Example payload:

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

### Airtel Money sandbox
Dedicated Airtel Money endpoints:
- `POST /api/v1/checkout/payments/airtel-money/initiate/`
- `GET /api/v1/checkout/payments/airtel-money/<reference>/status/`
- `POST /api/v1/payments/airtel-money/callback/`

Behavior:
- keeps Airtel Money flow separate from M-Pesa and card
- creates a pending Airtel Money collection session
- stores provider reference for callback reconciliation
- updates payment session to `paid` after successful callback
- allows order placement only after required payment completion

Required env vars:
- `AIRTEL_MONEY_SANDBOX_ENABLED`
- `AIRTEL_MONEY_PROVIDER_NAME`

Example payload:

```json
{
  "phone_number": "+254700000011",
  "payer_email": "buyer@example.com"
}
```

## 10) Inventory Reservation And Oversell Protection
Implemented:
- basket-level stock reservations tied to basket lines
- reservation release when basket lines are reduced or removed
- final locked stock validation before order placement
- automatic reservation release just before order creation so Oscar can convert stock to order allocations cleanly
- shipped order lines now consume allocated stock
- cancelled order lines now release allocated stock

Notes:
- basket responses now include `reserved_quantity` and `available_quantity` per line
- checkout blocks order placement if current stock can no longer satisfy the basket
- reorder skips lines that cannot be reserved because stock is no longer sufficient

## 11) Production-Grade Search Indexing
Implemented:
- OpenSearch is now the single live indexing path for product text and image metadata
- Haystack realtime signal processing is disabled to avoid the simple-backend `update is not implemented` warnings
- product create, update, delete, stock changes, image changes, attribute changes, and category changes now trigger index refresh
- product deletes now remove both the text-search document and the image-search document
- image index refresh distinguishes between:
  - metadata-only refreshes for stock/price/title/category changes
  - full embedding regeneration when the product image itself changes
- recommendation caches are cleared whenever product indexing is refreshed or removed

Command:

```powershell
python manage.py reindex_search_data
python manage.py reindex_search_data --batch-size 200 --limit 100
```

## 12) Shipping Rule Hardening
Implemented:
- centralized, data-driven shipping rule engine
- shipping eligibility based on:
  - destination country
  - basket subtotal
  - total basket weight
  - supplier count
  - project-logistics requirement
- carrier/service metadata on shipping methods
- ETA metadata on shipping methods
- payment/order validation to block checkout if shipping destination or method changed after payment initialization
- stronger shipping address validation for:
  - phone number requirement
  - postcode requirement for international shipping

Checkout shipping payload now includes:
- `metrics.item_count`
- `metrics.line_count`
- `metrics.supplier_count`
- `metrics.total_weight_kg`
- `metrics.requires_project_logistics`

Shipping methods now include:
- `carrier_code`
- `service_code`
- `method_type`
- `is_pickup`
- `eta.min_days`
- `eta.max_days`

## 13) Tax Rule Hardening
Implemented:
- rule-based tax configuration per country
- separate product-profile tax rates and shipping-profile tax rates
- support for tax-exempt product profiles such as:
  - `water_treatment_chemical`
  - `service`
- checkout tax breakdown now includes:
  - `default_rate`
  - `shipping_rate`
  - `shipping_profile`
  - `item_count`
  - `line_breakdown[]`
- order pricing now uses the same tax rule engine as checkout and payment initialization
- order payloads now expose `tax_code`

Current tax profile resolution:
- explicit product attribute `tax_profile` if present
- otherwise backend heuristics based on title

Current shipping tax profile resolution:
- derived from shipping method type such as:
  - `pickup`
  - `freight`
  - `express`
  - `project`

## 10) Image Embedding Settings
Environment variables:
- `IMAGE_EMBEDDING_BACKEND=clip` (`hash` is available fallback)
- `CLIP_MODEL_NAME=openai/clip-vit-base-patch32`
- `CLIP_DEVICE=cpu` (`auto`, `cpu`, `cuda`, `mps`)

Behavior:
- Product save triggers image-embedding indexing task.
- If product/image is missing, existing vector doc is removed.
- If CLIP backend fails to initialize, service falls back to hash embedding and logs the error.
- First CLIP usage downloads model weights and can be slower.

## 11) What Is Implemented vs Placeholder
Implemented:
- API wiring and service structure.
- Database fallback logic for all three features.
- OpenSearch-backed text/vector query paths.
- Real CLIP-based image embedding service with fallback.
- Image embedding index write + backfill command.

Placeholder:
- Better ranking rules and offline evaluation for recommendations.
- Full product ingestion pipeline with industrial attributes normalization.

## 12) Performance-first Next Tasks
1. Add query profiling and response-time metrics (p95 targets).
2. Add aggressive Redis caching for common search and recommendation queries.
3. Use exact part-number analyzers in OpenSearch and synonyms for industrial terms.
4. Add bulk indexing command for initial catalog load.
5. Add load tests for `/search`, `/search/image`, `/recommendations`.

## PostgreSQL Storage
- PostgreSQL data is stored in `../Database/postgres` (relative to `Backend`).

## CSV Importer
Use the management command below to bulk-load industrial products:

```powershell
python manage.py import_industrial_catalog industrial_catalog_template.csv --dry-run
python manage.py import_industrial_catalog industrial_catalog_template.csv
```

CSV minimum columns:
- `upc`
- `title`

Useful optional columns:
- `description`
- `category_path` (e.g. `Pumps > Hydraulic Pumps`)
- `price`
- `num_in_stock`
- `partner_sku`
- `currency`
- `is_public`
- `image_path` (single image file path)
- `image_paths` (multiple paths separated by `|` or `;`)
- `image_caption` (caption used with `image_path`)
- any `attr__*` columns for dynamic product attributes (e.g. `attr__brand`, `attr__moq`)

Image path notes:
- Relative paths are resolved from the CSV file folder.
- Re-import is idempotent by image content hash per product.

## Image Deduplication
If duplicate product images already exist from previous imports, clean them with:

```powershell
python manage.py dedupe_product_images --dry-run
python manage.py dedupe_product_images
```

Optional single-product cleanup:

```powershell
python manage.py dedupe_product_images --upc PN-1001
```
