import type { Options, RequestResult } from "@hey-api/client-fetch";

interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

interface PaginatedRequest {
  query?: {
    page?: number;
    // biome-ignore lint/style/useNamingConvention: api is in snake_case
    page_size?: number;
  };
}

type PaginatedEndpoint<T> = <ThrowOnError extends boolean = false>(
  options?: Options<PaginatedRequest, ThrowOnError>,
) => RequestResult<PaginatedResponse<T>, unknown, ThrowOnError>;

export const paginated = async <T>(
  endpoint: PaginatedEndpoint<T>,
  options?: PaginatedRequest,
) => {
  const maxPerPage = 199;
  options.query.page_size = maxPerPage;
  options.query.page = 1;

  const firstPage = (await endpoint(options)).data;
  const results = firstPage.results;

  const nbElements = firstPage.count;
  const nbPages = Math.ceil(nbElements / maxPerPage);

  if (nbPages > 1) {
    const promises: Promise<T[]>[] = [];
    for (let i = 2; i <= nbPages; i++) {
      const nextPage = structuredClone(options);
      nextPage.query.page = i;
      promises.push(endpoint(nextPage).then((res) => res.data.results));
    }
    results.push(...(await Promise.all(promises)).flat());
  }
  return results;
};
