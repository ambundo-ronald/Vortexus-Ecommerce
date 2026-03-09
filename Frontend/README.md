# Vortexus Frontend

Standalone frontend for the industrial marketplace.

## Stack
- Vite (vanilla JS)
- Custom CSS UI tuned for industrial ecommerce

## Run
1. Install dependencies:
   ```powershell
   & "C:\Program Files\nodejs\npm.cmd" install
   ```
2. (Optional) set API host:
   ```powershell
   Copy-Item .env.example .env
   ```
3. Start dev server:
   ```powershell
   & "C:\Program Files\nodejs\npm.cmd" run dev
   ```
4. Open:
   - `http://127.0.0.1:5173`

## Backend Dependency
Backend API should be running at `http://127.0.0.1:8000`:
- `GET /api/v1/search/`
- `POST /api/v1/search/image/`
- `GET /api/v1/recommendations/`
- `GET /api/v1/catalog/categories/`
- `GET /api/v1/catalog/products/`
- `GET /api/v1/catalog/products/<id>/`
- `POST /api/v1/quotes/`

## Frontend Routes
- `#/` Home (hero, recommendations, image search)
- `#/catalog` Product listing page (filters, chips, sorting, load more)
- `#/product/<id>` Product detail page (specs, related products, sticky mobile actions, quote form)
