import { DEFAULT_THRESHOLDS, SUMMARY_TREND_STATS, envNumber } from '../config.js';
import { hasCredentials } from '../lib/credentials.js';
import { discoverCatalog, requireCatalog } from '../lib/data.js';
import { summaryHandler } from '../lib/summary.js';
import { checkoutPreviewJourney } from '../workflows/checkout.js';

export const options = {
  scenarios: {
    checkout_preview: {
      executor: 'constant-vus',
      vus: envNumber('VUS', 5),
      duration: __ENV.DURATION || '1m',
      gracefulStop: '30s',
    },
  },
  thresholds: {
    ...DEFAULT_THRESHOLDS,
    checkout_preview_duration: ['p(95)<1200'],
  },
  summaryTrendStats: SUMMARY_TREND_STATS,
};

export function setup() {
  if (!hasCredentials()) {
    throw new Error(
      'Provide TEST_USER_EMAIL and TEST_USER_PASSWORD, or TEST_USERS_FILE. Test accounts must have email 2FA disabled.',
    );
  }
  return requireCatalog(discoverCatalog(), 'checkout preview testing');
}

export default function (catalog) {
  checkoutPreviewJourney(catalog);
}

export const handleSummary = summaryHandler('checkout-preview');
