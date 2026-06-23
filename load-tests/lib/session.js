import exec from 'k6/execution';

import { credentialsForVu } from './credentials.js';
import { apiRequest, getCsrfToken, parseJson } from './http.js';
import { accountDuration, businessErrors } from './metrics.js';

let csrfToken = null;
let authenticated = false;

export function csrf() {
  if (!csrfToken) csrfToken = getCsrfToken();
  return csrfToken;
}

export function loginCurrentVu() {
  if (authenticated) return true;

  const credentials = credentialsForVu(exec.vu.idInTest);
  if (!credentials?.identifier || !credentials?.password) {
    businessErrors.add(1);
    return false;
  }

  const response = apiRequest('POST', '/account/login/', {
    body: credentials,
    csrfToken: csrf(),
    expected: [200],
    name: 'account login',
    durationMetric: accountDuration,
  });
  const payload = parseJson(response, {});

  if (payload?.requires_2fa) {
    businessErrors.add(1);
    return false;
  }
  if (!payload?.user) return false;

  csrfToken = payload.csrf_token || csrfToken;
  authenticated = true;
  return true;
}
