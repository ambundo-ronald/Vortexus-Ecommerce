let users = [];

if (__ENV.TEST_USERS_FILE) {
  const loaded = JSON.parse(open(__ENV.TEST_USERS_FILE));
  users = Array.isArray(loaded) ? loaded : loaded.users || [];
} else if (__ENV.TEST_USER_EMAIL && __ENV.TEST_USER_PASSWORD) {
  users = [{
    identifier: __ENV.TEST_USER_EMAIL,
    password: __ENV.TEST_USER_PASSWORD,
  }];
}

export function hasCredentials() {
  return users.length > 0;
}

export function credentialsForVu(vuNumber) {
  if (!users.length) return null;
  const user = users[(vuNumber - 1) % users.length];
  return {
    identifier: user.identifier || user.email || user.username,
    password: user.password,
  };
}
