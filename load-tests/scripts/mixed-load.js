import { DEFAULT_THRESHOLDS, SUMMARY_TREND_STATS, envBoolean, envNumber } from '../config.js';
import { hasCredentials } from '../lib/credentials.js';
import { discoverCatalog, requireCatalog } from '../lib/data.js';
import { summaryHandler } from '../lib/summary.js';
import { accountJourney } from '../workflows/account.js';
import { cartJourney } from '../workflows/cart.js';
import { publicBrowse } from '../workflows/public.js';

const scenarios = {
  storefront_browsing: {
    executor: 'ramping-vus',
    exec: 'browseScenario',
    startVUs: 0,
    stages: [
      { duration: '30s', target: envNumber('BROWSE_VUS', 40) },
      { duration: __ENV.DURATION || '3m', target: envNumber('BROWSE_VUS', 40) },
      { duration: '30s', target: 0 },
    ],
    gracefulRampDown: '20s',
  },
  cart_activity: {
    executor: 'constant-vus',
    exec: 'cartScenario',
    vus: envNumber('CART_VUS', 8),
    duration: __ENV.DURATION || '3m',
    startTime: '20s',
    gracefulStop: '20s',
  },
};

if (envBoolean('INCLUDE_AUTH') && hasCredentials()) {
  scenarios.account_activity = {
    executor: 'constant-vus',
    exec: 'accountScenario',
    vus: envNumber('ACCOUNT_VUS', 5),
    duration: __ENV.DURATION || '3m',
    startTime: '20s',
    gracefulStop: '20s',
  };
}

export const options = {
  scenarios,
  thresholds: DEFAULT_THRESHOLDS,
  summaryTrendStats: SUMMARY_TREND_STATS,
};

export function setup() {
  return requireCatalog(discoverCatalog(), 'mixed load testing');
}

export function browseScenario(catalog) {
  publicBrowse(catalog);
}

export function cartScenario(catalog) {
  cartJourney(catalog);
}

export function accountScenario() {
  accountJourney();
}

export const handleSummary = summaryHandler('mixed-load');
