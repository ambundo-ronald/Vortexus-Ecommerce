import { DEFAULT_THRESHOLDS, SUMMARY_TREND_STATS, envNumber } from '../config.js';
import { discoverCatalog, requireCatalog } from '../lib/data.js';
import { summaryHandler } from '../lib/summary.js';
import { publicBrowse } from '../workflows/public.js';

const peakVus = envNumber('VUS', 100);

export const options = {
  stages: [
    { duration: __ENV.RAMP_UP || '30s', target: Math.max(1, Math.round(peakVus * 0.25)) },
    { duration: __ENV.STEADY_1 || '2m', target: Math.max(1, Math.round(peakVus * 0.5)) },
    { duration: __ENV.STEADY_2 || '2m', target: peakVus },
    { duration: __ENV.RAMP_DOWN || '30s', target: 0 },
  ],
  thresholds: DEFAULT_THRESHOLDS,
  summaryTrendStats: SUMMARY_TREND_STATS,
};

export function setup() {
  return requireCatalog(discoverCatalog(), 'public load testing');
}

export default function (catalog) {
  publicBrowse(catalog);
}

export const handleSummary = summaryHandler('public-load');
