import { products } from '../../../app/data/products';
import { handleTableQuery } from '~~/server/utils/tableQuery';

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
    data: products,
    query,
    searchableFields: ['name', 'sku', 'category', 'status'],
    customFilter: (item) => {
      // Only filter by category if provided
      if (query.category && query.category !== 'All' && item.category !== query.category) {
        return false;
      }
      return true;
    },
  });
});
