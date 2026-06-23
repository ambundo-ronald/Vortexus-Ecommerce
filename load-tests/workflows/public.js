import { group, sleep } from 'k6';

import { THINK_TIME_MAX, THINK_TIME_MIN } from '../config.js';
import { randomItem } from '../lib/data.js';
import { apiGet } from '../lib/http.js';
import { catalogDuration, searchDuration } from '../lib/metrics.js';

function think() {
  sleep(THINK_TIME_MIN + Math.random() * (THINK_TIME_MAX - THINK_TIME_MIN));
}

export function publicBrowse(catalog) {
  const productId = randomItem(catalog.productIds);
  const categorySlug = randomItem(catalog.categorySlugs);
  const query = encodeURIComponent(randomItem(catalog.productNames) || 'pump');

  group('homepage data', () => {
    apiGet('/content/marketing-blocks/', {
      name: 'marketing blocks',
      expected: [200],
      durationMetric: catalogDuration,
    });
    apiGet('/catalog/categories/', {
      name: 'catalog categories',
      expected: [200],
      durationMetric: catalogDuration,
    });
    apiGet('/recommendations/?limit=8', {
      name: 'recommendations',
      expected: [200],
      durationMetric: catalogDuration,
    });
    apiGet('/offers/?page=1&page_size=12', {
      name: 'public offers',
      expected: [200],
      durationMetric: catalogDuration,
    });
  });
  think();

  group('catalog browse', () => {
    const category = categorySlug ? `&category=${encodeURIComponent(categorySlug)}` : '';
    apiGet(`/catalog/products/?page=1&page_size=24&sort_by=relevance${category}`, {
      name: 'catalog products',
      expected: [200],
      durationMetric: catalogDuration,
    });
  });
  think();

  if (productId) {
    group('product detail', () => {
      apiGet(`/catalog/products/${productId}/`, {
        name: 'product detail',
        expected: [200],
        durationMetric: catalogDuration,
      });
      apiGet(`/catalog/products/${productId}/reviews/`, {
        name: 'product reviews',
        expected: [200],
        durationMetric: catalogDuration,
      });
    });
  }
  think();

  group('search', () => {
    apiGet(`/search/?q=${query}&page=1&page_size=24`, {
      name: 'product search',
      expected: [200],
      durationMetric: searchDuration,
    });
    apiGet(`/search/suggestions/?q=${query}&limit=8`, {
      name: 'search suggestions',
      expected: [200],
      durationMetric: searchDuration,
    });
    apiGet(`/search/facets/?q=${query}`, {
      name: 'search facets',
      expected: [200],
      durationMetric: searchDuration,
    });
  });
}
