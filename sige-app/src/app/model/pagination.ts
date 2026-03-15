export type PaginatedResponse<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};

export type PaginationParams = {
  page?: number;
  page_size?: number;
  search?: string;
  [key: string]: any;
};

export function normalizePaginatedResponse<T>(response: PaginatedResponse<T> | T[]): PaginatedResponse<T> {
  if (Array.isArray(response)) {
    return {
      count: response.length,
      next: null,
      previous: null,
      results: response,
    };
  }

  return {
    count: Number(response.count) || 0,
    next: response.next || null,
    previous: response.previous || null,
    results: response.results || [],
  };
}
