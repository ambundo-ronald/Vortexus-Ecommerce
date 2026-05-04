# Vortexus Frontend V1

React/Vite storefront scaffold for the Django Oscar backend in `../Backend`.

## Scope

This tree is intended to cover the backend API surface in agile slices:

- public catalog, search, image search, recommendations, quote requests
- session auth, customer profile, wishlist, reviews, order history
- basket, shipping, tax-aware checkout, payments, and order placement
- supplier profile, supplier products, supplier orders, supplier dashboard
- staff/admin product, order, user, media, settings, supplier, audit, and ERP integration management

## Backend Contract

Local backend:

```text
http://127.0.0.1:8000/api/v1
```

All mutating requests must use session cookies and `X-CSRFToken`. The shared API client in `src/api/axiosClient.js` centralizes that behavior.

## Start

```bash
cd frontendV1
npm install
npm run dev
```

The Vite dev server is configured for `http://127.0.0.1:5174`.


cd /home/newtonmanyisa/Vortexus-Ecommerce/Backend

docker compose stop postgres
docker compose rm -f postgres
docker compose up -d postgres
docker compose ps
cd /home/newtonmanyisa/Vortexus-Ecommerce/Backend
source .venv/bin/activate

python manage.py check
python manage.py migrate
python manage.py runserver 127.0.0.1:8000 --noreload
