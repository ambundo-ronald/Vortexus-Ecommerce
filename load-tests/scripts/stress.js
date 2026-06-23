import { DEFAULT_THRESHOLDS, SUMMARY_TREND_STATS, envNumber } from '../config.js';
import { discoverCatalog, requireCatalog } from '../lib/data.js';
import { summaryHandler } from '../lib/summary.js';
import { publicBrowse } from '../workflows/public.js';

const maximumVus = envNumber('VUS', 400);

export const options = {
  stages: [
    { duration: '1m', target: Math.max(1, Math.round(maximumVus * 0.125)) },
    { duration: '2m', target: Math.max(1, Math.round(maximumVus * 0.25)) },
    { duration: '2m', target: Math.max(1, Math.round(maximumVus * 0.5)) },
    { duration: '2m', target: maximumVus },
    { duration: '1m', target: 0 },
  ],
  thresholds: {
    ...DEFAULT_THRESHOLDS,
    http_req_failed: ['rate<0.05'],
    http_req_duration: ['p(95)<1500', 'p(99)<3000'],
  },
  summaryTrendStats: SUMMARY_TREND_STATS,
};

export function setup() {
  return requireCatalog(discoverCatalog(), 'stress testing');
}

export default function (catalog) {
  publicBrowse(catalog);
}

export const handleSummary = summaryHandler('stress');
