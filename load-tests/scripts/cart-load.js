import { DEFAULT_THRESHOLDS, SUMMARY_TREND_STATS, envNumber } from '../config.js';
import { discoverCatalog, requireCatalog } from '../lib/data.js';
import { summaryHandler } from '../lib/summary.js';
import { cartJourney } from '../workflows/cart.js';

const peakVus = envNumber('VUS', 20);

export const options = {
  stages: [
    { duration: __ENV.RAMP_UP || '20s', target: Math.max(1, Math.round(peakVus / 2)) },
    { duration: __ENV.DURATION || '2m', target: peakVus },
    { duration: __ENV.RAMP_DOWN || '20s', target: 0 },
  ],
  thresholds: {
    ...DEFAULT_THRESHOLDS,
    cart_write_duration: ['p(95)<1000'],
  },
  summaryTrendStats: SUMMARY_TREND_STATS,
};

export function setup() {
  return requireCatalog(discoverCatalog(), 'cart load testing');
}

export default function (catalog) {
  cartJourney(catalog);
}

export const handleSummary = summaryHandler('cart-load');
