import { group, sleep } from 'k6';

import { randomItem, findBasketLines, lineId } from '../lib/data.js';
import { apiGet, apiRequest, parseJson } from '../lib/http.js';
import { cartWriteDuration } from '../lib/metrics.js';
import { csrf } from '../lib/session.js';

export function cartJourney(catalog) {
  const productId = randomItem(catalog.productIds);
  if (!productId) return;

  let addedLineId = null;

  group('session cart', () => {
    apiGet('/checkout/basket/', {
      name: 'basket read',
      expected: [200],
    });

    const addResponse = apiRequest('POST', '/checkout/basket/items/', {
      body: { product_id: productId, quantity: 1 },
      csrfToken: csrf(),
      expected: [201],
      name: 'basket add item',
      durationMetric: cartWriteDuration,
    });
    const lines = findBasketLines(parseJson(addResponse, {}));
    addedLineId = lineId(lines[lines.length - 1]);

    apiGet('/checkout/basket/', {
      name: 'basket read after add',
      expected: [200],
    });
  });

  sleep(0.3);

  if (addedLineId) {
    apiRequest('DELETE', `/checkout/basket/items/${addedLineId}/`, {
      csrfToken: csrf(),
      expected: [200],
      name: 'basket remove item',
      durationMetric: cartWriteDuration,
    });
  }
}
