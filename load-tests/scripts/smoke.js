import { apiGet } from '../lib/http.js';
import { discoverCatalog, requireCatalog } from '../lib/data.js';
import { summaryHandler } from '../lib/summary.js';
import { cartJourney } from '../workflows/cart.js';
import { publicBrowse } from '../workflows/public.js';
import { DEFAULT_THRESHOLDS, SUMMARY_TREND_STATS } from '../config.js';

export const options = {
  vus: 1,
  iterations: 1,
  thresholds: DEFAULT_THRESHOLDS,
  summaryTrendStats: SUMMARY_TREND_STATS,
};

export function setup() {
  apiGet('/health/ready/', {
    name: 'health ready',
    expected: [200],
  });
  return requireCatalog(discoverCatalog(), 'the smoke test');
}

export default function (catalog) {
  publicBrowse(catalog);
  cartJourney(catalog);
}

export const handleSummary = summaryHandler('smoke');
