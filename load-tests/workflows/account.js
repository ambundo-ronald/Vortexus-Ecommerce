import { group, sleep } from 'k6';

import { apiGet } from '../lib/http.js';
import { accountDuration } from '../lib/metrics.js';
import { loginCurrentVu } from '../lib/session.js';

export function accountJourney() {
  if (!loginCurrentVu()) return;

  group('customer account', () => {
    apiGet('/account/me/', {
      name: 'account profile',
      expected: [200],
      durationMetric: accountDuration,
    });
    apiGet('/account/preferences/', {
      name: 'account preferences',
      expected: [200],
      durationMetric: accountDuration,
    });
    apiGet('/account/orders/', {
      name: 'account orders',
      expected: [200],
      durationMetric: accountDuration,
    });
    apiGet('/account/wishlist/', {
      name: 'account wishlist',
      expected: [200],
      durationMetric: accountDuration,
    });
    apiGet('/account/notifications/', {
      name: 'account notifications',
      expected: [200],
      durationMetric: accountDuration,
    });
    apiGet('/account/recently-viewed/', {
      name: 'recently viewed',
      expected: [200],
      durationMetric: accountDuration,
    });
  });

  sleep(0.5);
}
