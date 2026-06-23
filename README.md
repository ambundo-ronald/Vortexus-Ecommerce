# Vortexus Monorepo

Industrial ecommerce MVP split into:
- `frontendV1/` - primary storefront UI
- `Frontend/` - older standalone storefront UI
- `Backend/` - Django Oscar APIs, admin, catalog, search, recommendations
- `frappe_apps/vortexus_ecommerce_integration/` - optional ERPNext app for ecommerce source tracking, customer/order/invoice/payment sync, and inventory helpers

Launch checklist: [LAUNCH_PAYMENT_ERP_CHECKLIST.md](LAUNCH_PAYMENT_ERP_CHECKLIST.md)

## Quick Start (Local)

## 1) Backend
```powershell
cd Backend
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py runserver
```

Backend runs on `http://127.0.0.1:8000`

## 2) Frontend
```powershell
cd Frontend
npm install
npm run dev
```

Frontend runs on `http://127.0.0.1:5173`

Primary storefront V1:

```powershell
cd frontendV1
npm install
npm run dev
```

Frontend V1 runs on `http://127.0.0.1:5174`

## API Endpoints Used by Frontend
- `GET /api/v1/catalog/categories/`
- `GET /api/v1/catalog/products/`
- `GET /api/v1/catalog/products/<id>/`
- `POST /api/v1/quotes/`
- `GET /api/v1/search/`
- `POST /api/v1/search/image/`
- `GET /api/v1/recommendations/`

## Notes
- CORS is enabled in backend settings for:
  - `http://127.0.0.1:5173`
  - `http://localhost:5173`
- Frontend API host is configured by `Frontend/.env` using:
  - `VITE_API_BASE_URL=http://127.0.0.1:8000`

## Docker / VPS Deployment

The root `docker-compose.yml` runs the full stack:
- Django backend with Gunicorn
- Celery worker and Celery beat
- PostgreSQL
- Redis
- OpenSearch
- Vite storefront served by Nginx
- Nuxt dashboard generated as static files and served by Nginx
- Caddy reverse proxy with automatic HTTPS

### 1) Prepare production environment

```bash
cp .env.production.example .env.production
```

Edit `.env.production` and set real values for:
- `POSTGRES_PASSWORD`
- `DJANGO_SECRET_KEY`
- `STOREFRONT_DOMAIN`
- `DASHBOARD_DOMAIN`
- `API_DOMAIN`
- `DJANGO_ALLOWED_HOSTS`
- `CORS_ALLOWED_ORIGINS`
- `CSRF_TRUSTED_ORIGINS`
- payment, email, and ERPNext credentials as needed

For local Docker testing on Windows, use:

```powershell
Copy-Item .env.docker.local.example .env.docker.local
docker compose --env-file .env.docker.local config
```

The local Docker env uses:

```text
http://localhost:5174        -> storefront direct container port
http://localhost:3000        -> dashboard direct container port
http://localhost:8000        -> backend API direct container port
```

The Caddy proxy also serves `http://localhost` for the storefront. The direct ports are simpler on Windows because they do not require editing the hosts file for `api.localhost` and `dashboard.localhost`.

Recommended domain layout:

```text
vortexus.example.com        -> storefront
admin.vortexus.example.com  -> dashboard
api.vortexus.example.com    -> Django API/admin/static/media
```

### 2) Build and start infrastructure

```bash
docker compose --env-file .env.production build
docker compose --env-file .env.production up -d postgres redis opensearch
```

### 3) Initialize Django

```bash
docker compose --env-file .env.production run --rm backend python manage.py migrate
docker compose --env-file .env.production run --rm backend python manage.py collectstatic --noinput
docker compose --env-file .env.production run --rm backend python manage.py bootstrap_search_indices
docker compose --env-file .env.production run --rm backend python manage.py createsuperuser
```

Optional seed/index commands:

```bash
docker compose --env-file .env.production run --rm backend python manage.py bootstrap_demo_data
docker compose --env-file .env.production run --rm backend python manage.py reindex_search_data
docker compose --env-file .env.production run --rm backend python manage.py backfill_image_embeddings --sync
```

The default backend image skips heavy ML packages so production builds stay small and predictable. Install `Backend/requirements-ml.txt` only on workers or one-off jobs that need CLIP/photo embedding generation.

### 4) Start the whole stack

```bash
docker compose --env-file .env.production up -d
```

Useful checks:

```bash
docker compose ps
docker compose logs -f backend
docker compose logs -f celery-worker
```

Backend health endpoints:

```text
https://api.vortexus.example.com/api/v1/health/live/
https://api.vortexus.example.com/api/v1/health/ready/
```

### VPS notes

- Point the three DNS records to the VPS before starting Caddy for real HTTPS.
- Open ports `80` and `443` on the VPS firewall.
- OpenSearch commonly needs `vm.max_map_count=262144` on Linux hosts.
- OpenSearch and CLIP/PyTorch are memory-hungry. A 4 GB RAM VPS is the practical minimum; 8 GB is safer.
- Keep `.env.production` out of git. It is intentionally ignored.

### Launch-critical payments and ERPNext

Before opening checkout to customers, confirm these are set with real production values:

- `PESAPAL_CONSUMER_KEY`, `PESAPAL_CONSUMER_SECRET`, `PESAPAL_ENVIRONMENT`, `PESAPAL_IPN_URL`, and `PESAPAL_CANCELLATION_URL`.
- `MPESA_*` values only if M-Pesa is enabled in the dashboard.
- `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`, and payment callback URLs must use the public storefront/API domains.
- Admin payment configuration should show only the methods you want customers to use.

When an order is placed, the backend now queues an ERPNext Sales Order export after the checkout transaction commits. Active ERPNext connections export orders unless their metadata contains `"export_orders": false`.

Recommended ERPNext connection metadata for launch:

```json
{
  "export_orders": true,
  "export_order_accounting": true,
  "sync_cancellations": true,
  "sync_customers": true,
  "use_vortexus_bridge_app": true,
  "default_customer": "Vortexus Online Customer",
  "customer_group": "Ecommerce",
  "territory": "Kenya",
  "pesapal_bank_account": "Pesapal Clearing - VI",
  "delivery_days": 7
}
```

Set `"use_vortexus_bridge_app": true` only after installing `frappe_apps/vortexus_ecommerce_integration` into ERPNext. Without that flag, the backend uses the direct ERPNext resource API for order export.

For reliable fulfillment export, make sure the ERPNext customer exists and imported products have ERPNext item mappings. If a product has no ERPNext mapping, the exporter falls back to the order line partner SKU or UPC; if none exists, the export fails loudly in integration logs instead of silently dropping the order.

With the bridge app enabled, paid orders queue Sales Invoice and Payment Entry creation after the payment and order are linked. Admin cancellations queue ERPNext Sales Order/Sales Invoice cancellation. Staff can also queue ERPNext credit-note creation for a paid payment:

```text
POST /api/v1/admin/payments/<payment_reference>/refund/
```

This creates the ERPNext accounting-side credit note through the bridge app. Actual Pesapal money movement still needs to be handled according to Pesapal refund operations and reconciled against the ERPNext credit note.
For Pesapal payments, the admin refund endpoint submits Pesapal's API 3.0 refund request first using the stored confirmation code, then queues the ERPNext credit note after Pesapal accepts the request. Pesapal's successful refund request response means the refund has been received for processing; finance should still reconcile final settlement.

## Cloudflare Tunnel Preview

For a stable public preview URL from a local Docker stack, use the optional `cloudflared` compose profile. Cloudflare terminates public HTTPS, and the local Caddy container routes plain HTTP traffic inside Docker.

1. In Cloudflare Zero Trust, create a tunnel and add three public hostnames:
   - `vortexus.example.com` -> `http://caddy:80`
   - `admin.vortexus.example.com` -> `http://caddy:80`
   - `api.vortexus.example.com` -> `http://caddy:80`
2. Copy `.env.cloudflare.example` to `.env.cloudflare`.
3. Copy `.env.cloudflare.app.example` to `.env.cloudflare.app`.
4. Set the real `STOREFRONT_DOMAIN`, `DASHBOARD_DOMAIN`, `API_DOMAIN`, `VITE_API_BASE_URL`, and `NUXT_PUBLIC_API_BASE` in `.env.cloudflare`.
5. Set the matching `DJANGO_ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`, payment callbacks, and app secrets in `.env.cloudflare.app`.
6. Paste the connector token into `CLOUDFLARE_TUNNEL_TOKEN` in `.env.cloudflare`.
7. Start the stack:

```powershell
docker compose -f docker-compose.yml -f docker-compose.cloudflare.yml --env-file .env.cloudflare --profile tunnel up -d --build
```

The tunnel is outbound-only, so your local IP can change without changing the public URLs.

If you run Caddy without the Cloudflare override file and ports `80` or `443` are already in use, set alternate host ports in your env file:

```env
CADDY_HTTP_PORT=8080
CADDY_HTTPS_PORT=8443
```
