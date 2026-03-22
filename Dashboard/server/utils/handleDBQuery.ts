import { and, asc, count, desc, like, or, SQL, sql } from 'drizzle-orm';
import { SqliteTable } from 'drizzle-orm/sqlite-core'; // Changed from pg-core
import { useDB } from './db'; // Assuming useDB() provides your Drizzle SQLite instance

type TableQueryResult = {
    data: any[]; // Replace with specific type if known
}

// Define a robust and type-safe options interface using generics
interface TableQueryOptions<TTable extends SqliteTable> {
  /** The raw query parameters from the request. */
  query: Record<string, string | string[] | undefined>;

  /** The Drizzle SQLite table schema object itself (e.g., `users`). */
  table: TTable;

  /** An array of column names that should be searched. */
  searchableFields?: (keyof TTable['$inferSelect'])[];

  /** A function to generate a custom filter SQL expression. */
  getCustomFilter?: (search: string) => SQL | undefined;
}

/**
 * Handles dynamic table querying for SQLite with pagination, searching, and sorting.
 *
 * @template TTable - The type of the Drizzle SQLite table (e.g., typeof users).
 * @returns {Promise<TableQueryResult<TTable['$inferSelect']>>} The paginated query result.
 */
export async function handleTableQuery<TTable extends SqliteTable>({
  query,
  table,
  searchableFields,
  getCustomFilter,
}: TableQueryOptions<TTable>): Promise<TableQueryResult<TTable['$inferSelect']>> {
  const db = useDB();

  // --- 1. Parse and Sanitize Input ---
  const page = Number(query.page) || 1;
  const pageSize = Number(query.pageSize) || 10;
  const search = (query.search as string) || '';
  const sortBy = query.sortBy as keyof TTable['$inferSelect'] | undefined;
  const sortDir = query.sortDir === 'desc' ? 'desc' : 'asc';

  const whereConditions: (SQL | undefined)[] = [];

  // --- 2. Build Filter Conditions ---

  // Add custom filter if provided
  if (getCustomFilter) {
    whereConditions.push(getCustomFilter(search));
  }

  // Add search filter if search term and searchable fields are provided
  if (search && searchableFields?.length) {
    const searchTerm = `%${search.toLowerCase()}%`; // Lowercase the search term once

    const searchConditions = searchableFields
      // Ensure the column exists on the table before trying to use it
      .filter(field => table[field as string])
      .map(field =>
        // Use `like` with `lower()` for case-insensitive search in SQLite
        like(sql`lower(${table[field as string]})`, searchTerm)
      );

    if (searchConditions.length > 0) {
      whereConditions.push(or(...searchConditions));
    }
  }

  const finalWhereCondition = and(...whereConditions.filter(Boolean) as SQL[]);
  
  // --- 3. Build and Execute Queries in Parallel ---

  // Query for total items (using Drizzle's count() helper)
  const totalItemsQuery = db
    .select({ value: count() })
    .from(table)
    .where(finalWhereCondition);
  
  // Base query for fetching data
  const baseDataQuery = db.select().from(table).where(finalWhereCondition);

  // Run both queries concurrently for better performance
  const [[{ value: totalItems }], data] = await Promise.all([
    totalItemsQuery,
    (() => {
        let dataQuery = baseDataQuery;
        // Apply sorting
        if (sortBy && table[sortBy as string]) {
            const column = table[sortBy as string];
            dataQuery = dataQuery.orderBy(sortDir === 'asc' ? asc(column) : desc(column));
        }
        // Apply pagination
        return dataQuery.limit(pageSize).offset((page - 1) * pageSize);
    })()
  ]);

  return {
    data: data as TTable['$inferSelect'][],
    totalItems,
    currentPage: page,
    pageSize,
    totalPages: Math.ceil(totalItems / pageSize),
  };
}