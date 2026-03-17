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
- `GET|POST|PATCH /api/v1/supplier/profile/`
- `GET /api/v1/supplier/dashboard/`
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
- supplier-owned product CRUD via supplier partner stock records
- safe supplier delete behavior:
  - removes only the supplier's own offer
  - deletes the product only if no supplier offers remain

Approval options:
- Django admin: `Supplier Profiles`
- API: `PATCH /api/v1/admin/suppliers/<id>/`

## 7) Image Embedding Settings
Environment variables:
- `IMAGE_EMBEDDING_BACKEND=clip` (`hash` is available fallback)
- `CLIP_MODEL_NAME=openai/clip-vit-base-patch32`
- `CLIP_DEVICE=cpu` (`auto`, `cpu`, `cuda`, `mps`)

Behavior:
- Product save triggers image-embedding indexing task.
- If product/image is missing, existing vector doc is removed.
- If CLIP backend fails to initialize, service falls back to hash embedding and logs the error.
- First CLIP usage downloads model weights and can be slower.

## 8) What Is Implemented vs Placeholder
Implemented:
- API wiring and service structure.
- Database fallback logic for all three features.
- OpenSearch-backed text/vector query paths.
- Real CLIP-based image embedding service with fallback.
- Image embedding index write + backfill command.

Placeholder:
- Better ranking rules and offline evaluation for recommendations.
- Full product ingestion pipeline with industrial attributes normalization.

## 9) Performance-first Next Tasks
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
