import { orders } from '~/data/orderData';

const validSortFields = [
  'id',
  'orderNo',
  'companyName',
  'status',
  'packaged',
  'fulfilled',
  'invoiced',
  'paid',
  'orderTotal',
  'createdDate',
  'lastUpdated',
];

export default defineEventHandler((event) => {
  const query = getQuery(event);
  const page = Number(query.page) || 1;
  const pageSize = Number(query.pageSize) || 10;
  const search = (query.search || '').toString().toLowerCase();
  const sortByRaw = typeof query.sortBy === 'string' ? query.sortBy : '';
  const sortBy = validSortFields.includes(sortByRaw) ? sortByRaw : 'id';
  const sortDir = query.sortDir === 'desc' ? 'desc' : 'asc';

  let filtered = orders;
  if (search) {
    filtered = filtered.filter(order =>
      order.companyName.toLowerCase().includes(search) ||
      order.orderNo.toLowerCase().includes(search) ||
      order.status.toLowerCase().includes(search) ||
      String(order.id).includes(search)
    );
  }

  filtered = filtered.sort((a, b) => {
    let aVal = a[sortBy as keyof typeof a];
    let bVal = b[sortBy as keyof typeof b];
    if (typeof aVal === 'string') aVal = aVal.toLowerCase();
    if (typeof bVal === 'string') bVal = bVal.toLowerCase();
    if (aVal < bVal) return sortDir === 'asc' ? -1 : 1;
    if (aVal > bVal) return sortDir === 'asc' ? 1 : -1;
    return 0;
  });

  const totalItems = filtered.length;
  const paged = filtered.slice((page - 1) * pageSize, page * pageSize);

  return {
    data: paged,
    totalItems,
    currentPage: page,
    pageSize,
  };
});
