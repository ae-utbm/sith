import type { Client, RequestResult, TDataShape } from "#openapi:client";
import { type Options, client } from "#openapi";

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface PaginatedRequest {
  query?: {
    page?: number;
    // biome-ignore lint/style/useNamingConvention: api is in snake_case
    page_size?: number;
  };
  url: string;
}

type PaginatedEndpoint<T> = <ThrowOnError extends boolean = false>(
  options?: Options<PaginatedRequest, ThrowOnError>,
) => RequestResult<PaginatedResponse<T>, unknown, ThrowOnError>;

// TODO : If one day a test workflow is made for JS in this project
//  please test this function. A all cost.
/**
 * Load complete dataset from paginated routes.
 */
export const paginated = async <T>(
  endpoint: PaginatedEndpoint<T>,
  options?: PaginatedRequest,
): Promise<T[]> => {
  const maxPerPage = 200;
  const queryParams = options ?? ({} as PaginatedRequest);
  queryParams.query = queryParams.query ?? {};
  queryParams.query.page_size = maxPerPage;
  queryParams.query.page = 1;

  const firstPage = (await endpoint(queryParams)).data;
  const results = firstPage.results;

  const nbElements = firstPage.count;
  const nbPages = Math.ceil(nbElements / maxPerPage);

  if (nbPages > 1) {
    const promises: Promise<T[]>[] = [];
    for (let i = 2; i <= nbPages; i++) {
      const nextPage = structuredClone(queryParams);
      nextPage.query.page = i;
      promises.push(endpoint(nextPage).then((res) => res.data.results));
    }
    results.push(...(await Promise.all(promises)).flat());
  }
  return results;
};

interface Request extends TDataShape {
  client?: Client;
}

interface InterceptorOptions {
  url: string;
}

type GenericEndpoint = <ThrowOnError extends boolean = false>(
  options?: Options<Request, ThrowOnError>,
) => RequestResult<unknown, unknown, ThrowOnError>;

/**
 * Return the endpoint url of the endpoint
 **/
export const makeUrl = async (endpoint: GenericEndpoint) => {
  let url = "";
  const interceptor = (_request: undefined, options: InterceptorOptions) => {
    url = options.url;
    throw new Error("We don't want to send the request");
  };

  client.interceptors.request.use(interceptor);
  try {
    await endpoint({ client: client });
  } catch (_error) {
    /* do nothing */
  }
  client.interceptors.request.eject(interceptor);
  return url;
};
