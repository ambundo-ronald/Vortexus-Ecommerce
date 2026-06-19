import { DEFAULT_THRESHOLDS, SUMMARY_TREND_STATS, envNumber } from '../config.js';
import { discoverCatalog, requireCatalog } from '../lib/data.js';
import { summaryHandler } from '../lib/summary.js';
import { publicBrowse } from '../workflows/public.js';

export const options = {
  scenarios: {
    sustained_browsing: {
      executor: 'constant-vus',
      vus: envNumber('VUS', 50),
      duration: __ENV.DURATION || '30m',
      gracefulStop: '30s',
    },
  },
  thresholds: DEFAULT_THRESHOLDS,
  summaryTrendStats: SUMMARY_TREND_STATS,
};

export function setup() {
  return requireCatalog(discoverCatalog(), 'soak testing');
}

export default function (catalog) {
  publicBrowse(catalog);
}

export const handleSummary = summaryHandler('soak');
