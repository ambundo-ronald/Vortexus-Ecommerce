import { apiGet, parseJson } from './http.js';
import { catalogDuration } from './metrics.js';

export function collectionItems(payload) {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.results)) return payload.results;
  if (Array.isArray(payload?.products)) return payload.products;
  if (Array.isArray(payload?.categories)) return payload.categories;
  return [];
}

export function randomItem(items) {
  if (!items?.length) return null;
  return items[Math.floor(Math.random() * items.length)];
}

export function discoverCatalog() {
  const productsResponse = apiGet('/catalog/products/?in_stock=true&page=1&page_size=50', {
    name: 'setup available products',
    expected: [200],
    durationMetric: catalogDuration,
  });
  const categoriesResponse = apiGet('/catalog/categories/', {
    name: 'setup categories',
    expected: [200],
    durationMetric: catalogDuration,
  });

  const products = collectionItems(parseJson(productsResponse, {}));
  const categories = collectionItems(parseJson(categoriesResponse, {}));

  return {
    ready: productsResponse.status === 200 && categoriesResponse.status === 200,
    setupStatuses: {
      products: productsResponse.status,
      categories: categoriesResponse.status,
    },
    productIds: products.map((product) => product.id).filter(Boolean),
    productNames: products.map((product) => product.title || product.name).filter(Boolean),
    categorySlugs: categories.map((category) => category.slug).filter(Boolean),
  };
}

export function requireCatalog(catalog, purpose = 'load testing') {
  if (!catalog?.ready) {
    const productsStatus = catalog?.setupStatuses?.products || 'connection failed';
    const categoriesStatus = catalog?.setupStatuses?.categories || 'connection failed';
    throw new Error(
      `Preflight failed for ${purpose}. Product status: ${productsStatus}; category status: ${categoriesStatus}. ` +
      'Start Django with config.settings.performance and run smoke.js before increasing load.',
    );
  }
  if (!catalog.productIds.length) {
    throw new Error(
      `Preflight failed for ${purpose}: the API returned no in-stock products.`,
    );
  }
  return catalog;
}

export function findBasketLines(payload) {
  const basket = payload?.basket || payload;
  return basket?.lines || basket?.items || [];
}

export function lineId(line) {
  return line?.id || line?.line_id || null;
}
