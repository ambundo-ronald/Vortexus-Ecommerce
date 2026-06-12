import { Counter, Rate, Trend } from 'k6/metrics';

export const businessErrors = new Rate('business_errors');
export const throttledRequests = new Rate('throttled_requests');
export const unexpectedStatuses = new Counter('unexpected_statuses');
export const catalogDuration = new Trend('catalog_duration', true);
export const searchDuration = new Trend('search_duration', true);
export const cartWriteDuration = new Trend('cart_write_duration', true);
export const accountDuration = new Trend('account_duration', true);
export const checkoutPreviewDuration = new Trend('checkout_preview_duration', true);

export function recordResponse(response, expectedStatuses, durationMetric) {
  const accepted = expectedStatuses.includes(response.status);
  const throttled = response.status === 429;

  businessErrors.add(accepted ? 0 : 1);
  throttledRequests.add(throttled ? 1 : 0);
  if (!accepted) unexpectedStatuses.add(1);
  if (durationMetric) durationMetric.add(response.timings.duration);

  return accepted;
}
