import { users } from '../../../app/data/users';

export default eventHandler((event) => {
  const rawQuery = getQuery(event);
  const query: Record<string, string | string[] | undefined> = {};
  for (const key in rawQuery) {
    const value = rawQuery[key];
    if (typeof value === 'string' || Array.isArray(value) || typeof value === 'undefined') {
      query[key] = value;
    }
  }
  return handleTableQuery({
    data: users,
    query,
    searchableFields: ['name', 'email', 'id'],
  });
});