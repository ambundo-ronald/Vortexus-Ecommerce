const configuredBaseUrl = __ENV.BASE_URL || 'http://127.0.0.1:8000/api/v1';
const trimmedBaseUrl = configuredBaseUrl.replace(/\/+$/, '');

export const BASE_URL = /\/api\/v1$/i.test(trimmedBaseUrl)
  ? trimmedBaseUrl
  : `${trimmedBaseUrl}/api/v1`;
export const THINK_TIME_MIN = Number(__ENV.THINK_TIME_MIN || 0.4);
export const THINK_TIME_MAX = Number(__ENV.THINK_TIME_MAX || 1.2);

export const DEFAULT_THRESHOLDS = {
  checks: ['rate>0.99'],
  http_req_failed: ['rate<0.01'],
  http_req_duration: ['p(95)<800', 'p(99)<1500'],
  business_errors: ['rate<0.01'],
  throttled_requests: ['rate<0.01'],
};

export const SUMMARY_TREND_STATS = [
  'avg',
  'med',
  'p(90)',
  'p(95)',
  'p(99)',
  'max',
];

export function apiUrl(path) {
  return `${BASE_URL}${path.startsWith('/') ? path : `/${path}`}`;
}

export function envNumber(name, fallback) {
  const value = Number(__ENV[name]);
  return Number.isFinite(value) && value >= 0 ? value : fallback;
}

export function envBoolean(name, fallback = false) {
  const value = __ENV[name];
  if (value === undefined) return fallback;
  return ['1', 'true', 'yes', 'on'].includes(String(value).toLowerCase());
}
