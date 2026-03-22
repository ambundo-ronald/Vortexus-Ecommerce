interface FilterCondition {
  [fieldName: string]: {
    [operator: string]: string | string[];
  };
}


interface TableQueryOptions<T extends object> {
  data: T[];
  query: Record<string, string | string[] | undefined>;
  searchableFields?: (keyof T)[];
  customFilter?: (item: T, search: string) => boolean;
}

export function handleTableQuery<T extends object>({ data, query, searchableFields }: TableQueryOptions<T>) {
  const page = parseInt(query.page as string || '1');
  const pageSize = parseInt(query.pageSize as string || '10');
  const search = (query.search as string || '').toLowerCase();
  const sortBy = query.sortBy as keyof T || '';
  const sortDir = query.sortDir === 'desc' ? 'desc' : 'asc';

  let result: T[] = data;

  const filters = query.filter as FilterCondition | undefined;

  if (filters) {
    result = result.filter((item) => {
      let passesAllFilters = true;
      for (const fieldName in filters) {
        if (!passesAllFilters) break; 

        const fieldFilters = filters[fieldName];
        const itemValue = item[fieldName as keyof T];

        for (const operator in fieldFilters) {
          const filterValue = fieldFilters[operator];

          switch (operator) {
            case 'eq': 
              if (String(itemValue).toLowerCase() !== String(filterValue).toLowerCase()) {
                passesAllFilters = false;
              }
              break;
            case 'ne': 
                if (String(itemValue).toLowerCase() === String(filterValue).toLowerCase()) {
                    passesAllFilters = false;
                }
                break;
            case 'gt': 
              if (typeof itemValue === 'number' && typeof filterValue === 'string' && itemValue <= parseFloat(filterValue)) {
                passesAllFilters = false;
              }
              break;
            case 'lt': 
              if (typeof itemValue === 'number' && typeof filterValue === 'string' && itemValue >= parseFloat(filterValue)) {
                passesAllFilters = false;
              }
              break;
            case 'gte': 
              if (typeof itemValue === 'number' && typeof filterValue === 'string' && itemValue < parseFloat(filterValue)) {
                passesAllFilters = false;
              }
              break;
            case 'lte': 
              if (typeof itemValue === 'number' && typeof filterValue === 'string' && itemValue > parseFloat(filterValue)) {
                passesAllFilters = false;
              }
              break;
            case 'contains': 
              if (typeof itemValue === 'string' && typeof filterValue === 'string' && !itemValue.toLowerCase().includes(filterValue.toLowerCase())) {
                passesAllFilters = false;
              }
              break;
            case 'startsWith':
                if (typeof itemValue === 'string' && typeof filterValue === 'string' && !itemValue.toLowerCase().startsWith(filterValue.toLowerCase())) {
                    passesAllFilters = false;
                }
                break;
            case 'endsWith':
                if (typeof itemValue === 'string' && typeof filterValue === 'string' && !itemValue.toLowerCase().endsWith(filterValue.toLowerCase())) {
                    passesAllFilters = false;
                }
                break;
            case 'in': 
              if (typeof itemValue === 'string' && typeof filterValue === 'string') {
                const values = filterValue.split(',').map(v => v.trim().toLowerCase());
                if (!values.includes(itemValue.toLowerCase())) {
                  passesAllFilters = false;
                }
              } else if (isArray(itemValue) && typeof filterValue === 'string') { 
                const values = filterValue.split(',').map(v => v.trim().toLowerCase());
                const itemArray = itemValue.map(v => String(v).toLowerCase());
                if (!values.some(val => itemArray.includes(val))) { 
                    passesAllFilters = false;
                }
              }
              break;
            default:
              break;
          }
          if (!passesAllFilters) break; 
        }
      }
      return passesAllFilters;
    });
  }

  if (search && searchableFields && searchableFields.length > 0) {
    result = result.filter((item) =>
      searchableFields.some((field) => {
        const value = item[field];
        return typeof value === 'string' && value.toLowerCase().includes(search);
      })
    );
  }

  if (sortBy && result.length > 0 && sortBy in result[0]) {
    result.sort((a, b) => {
      const aValue = a[sortBy];
      const bValue = b[sortBy];
      if (aValue == null && bValue == null) return 0;
      if (aValue == null) return 1;
      if (bValue == null) return -1;
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        return sortDir === 'asc' ? aValue.localeCompare(bValue) : bValue.localeCompare(aValue);
      }
      if (sortDir === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });
  }

  const totalItems = result.length;
  const totalPages = Math.ceil(totalItems / pageSize);
  const offset = (page - 1) * pageSize;
  const paginatedData = result.slice(offset, offset + pageSize);

  return {
    data: paginatedData,
    totalItems,
    currentPage: page,
    pageSize,
    totalPages,
  };
}