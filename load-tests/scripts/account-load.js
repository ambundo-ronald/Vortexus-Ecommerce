import { DEFAULT_THRESHOLDS, SUMMARY_TREND_STATS, envNumber } from '../config.js';
import { hasCredentials } from '../lib/credentials.js';
import { summaryHandler } from '../lib/summary.js';
import { accountJourney } from '../workflows/account.js';

export const options = {
  scenarios: {
    account_reads: {
      executor: 'constant-vus',
      vus: envNumber('VUS', 10),
      duration: __ENV.DURATION || '2m',
      gracefulStop: '20s',
    },
  },
  thresholds: {
    ...DEFAULT_THRESHOLDS,
    account_duration: ['p(95)<800'],
  },
  summaryTrendStats: SUMMARY_TREND_STATS,
};

export function setup() {
  if (!hasCredentials()) {
    throw new Error(
      'Provide TEST_USER_EMAIL and TEST_USER_PASSWORD, or TEST_USERS_FILE. Test accounts must have email 2FA disabled.',
    );
  }
  return {};
}

export default function () {
  accountJourney();
}

export const handleSummary = summaryHandler('account-load');
