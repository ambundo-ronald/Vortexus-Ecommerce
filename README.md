# Vortexus Monorepo

Industrial ecommerce MVP split into:
- `Frontend/` - standalone storefront UI
- `Backend/` - Django Oscar APIs, admin, catalog, search, recommendations

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
