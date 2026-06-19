import { group, sleep } from 'k6';

import { randomItem, findBasketLines, lineId } from '../lib/data.js';
import { apiGet, apiRequest, parseJson } from '../lib/http.js';
import { cartWriteDuration, checkoutPreviewDuration } from '../lib/metrics.js';
import { csrf, loginCurrentVu } from '../lib/session.js';

const shippingAddress = {
  first_name: 'Load',
  last_name: 'Tester',
  line1: 'Performance Test Address',
  line2: '',
  line3: '',
  line4: 'Nairobi',
  state: 'Nairobi',
  postcode: '00100',
  country_code: 'KE',
  phone_number: '+254700000000',
  notes: 'Automated checkout preview load test. Do not dispatch.',
};

function shippingMethods(payload) {
  return payload?.shipping?.methods || payload?.methods || [];
}

export function checkoutPreviewJourney(catalog) {
  if (!loginCurrentVu()) return;

  const productId = randomItem(catalog.productIds);
  if (!productId) return;

  let addedLineId = null;

  group('checkout preview', () => {
    const addResponse = apiRequest('POST', '/checkout/basket/items/', {
      body: { product_id: productId, quantity: 1 },
      csrfToken: csrf(),
      expected: [201],
      name: 'checkout basket add',
      durationMetric: cartWriteDuration,
    });
    const lines = findBasketLines(parseJson(addResponse, {}));
    addedLineId = lineId(lines[lines.length - 1]);
    if (!addedLineId) return;

    apiRequest('PUT', '/checkout/shipping/address/', {
      body: shippingAddress,
      csrfToken: csrf(),
      expected: [200],
      name: 'checkout shipping address',
      durationMetric: checkoutPreviewDuration,
    });

    const shippingResponse = apiGet('/checkout/shipping/', {
      name: 'checkout shipping methods',
      expected: [200],
      durationMetric: checkoutPreviewDuration,
    });
    const method = shippingMethods(parseJson(shippingResponse, {}))[0];
    const methodCode = method?.code || method?.method_code;

    if (methodCode) {
      apiRequest('POST', '/checkout/shipping/select/', {
        body: { method_code: methodCode },
        csrfToken: csrf(),
        expected: [200],
        name: 'checkout select shipping',
        durationMetric: checkoutPreviewDuration,
      });
    }

    apiGet('/checkout/preview/', {
      name: 'checkout preview',
      expected: [200],
      durationMetric: checkoutPreviewDuration,
    });
  });

  sleep(0.4);

  if (addedLineId) {
    apiRequest('DELETE', `/checkout/basket/items/${addedLineId}/`, {
      csrfToken: csrf(),
      expected: [200],
      name: 'checkout cleanup basket',
      durationMetric: cartWriteDuration,
    });
  }
}
