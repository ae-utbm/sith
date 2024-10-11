import type { Client, Options, RequestResult } from "@hey-api/client-fetch";
import { client } from "#openapi";

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

// TODO : If one day a test workflow is made for JS in this project
//  please test this function. A all cost.
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

interface Request {
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
