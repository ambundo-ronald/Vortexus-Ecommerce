import { DEFAULT_THRESHOLDS, SUMMARY_TREND_STATS, envNumber } from '../config.js';
import { discoverCatalog, requireCatalog } from '../lib/data.js';
import { summaryHandler } from '../lib/summary.js';
import { publicBrowse } from '../workflows/public.js';

const spikeVus = envNumber('VUS', 500);

export const options = {
  stages: [
    { duration: '30s', target: 10 },
    { duration: '10s', target: spikeVus },
    { duration: '1m', target: spikeVus },
    { duration: '10s', target: 10 },
    { duration: '30s', target: 0 },
  ],
  thresholds: {
    ...DEFAULT_THRESHOLDS,
    http_req_failed: ['rate<0.05'],
    http_req_duration: ['p(95)<2000', 'p(99)<4000'],
  },
  summaryTrendStats: SUMMARY_TREND_STATS,
};

export function setup() {
  return requireCatalog(discoverCatalog(), 'spike testing');
}

export default function (catalog) {
  publicBrowse(catalog);
}

export const handleSummary = summaryHandler('spike');
