import http from 'k6/http';
import { check } from 'k6';

import { apiUrl } from '../config.js';
import { recordResponse } from './metrics.js';

export function parseJson(response, fallback = null) {
  try {
    return response.json();
  } catch (_) {
    return fallback;
  }
}

export function apiRequest(method, path, options = {}) {
  const {
    body = null,
    csrfToken = null,
    expected = [200],
    name = `${method} ${path}`,
    tags = {},
    durationMetric = null,
  } = options;

  const headers = { Accept: 'application/json' };
  let encodedBody = null;

  if (body !== null) {
    headers['Content-Type'] = 'application/json';
    encodedBody = JSON.stringify(body);
  }
  if (csrfToken) headers['X-CSRFToken'] = csrfToken;

  const response = http.request(method, apiUrl(path), encodedBody, {
    headers,
    tags: { name, ...tags },
  });
  const accepted = recordResponse(response, expected, durationMetric);

  check(response, {
    [`${name}: expected status`]: () => accepted,
  });

  return response;
}

export function apiGet(path, options = {}) {
  return apiRequest('GET', path, options);
}

export function getCsrfToken() {
  const response = apiGet('/account/csrf/', {
    name: 'account csrf',
    expected: [200],
  });
  return parseJson(response, {})?.csrf_token || null;
}
