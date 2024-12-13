import { History, getCurrentUrlParams, updateQueryString } from "#core:utils/history";
import {
  type ProductSchema,
  productSearchProductsDetailed,
  type ProductSearchProductsDetailedData,
} from "#openapi";

type ProductType = string;
type GroupedProducts = Record<ProductType, ProductSchema[]>;

const defaultPageSize = 100;
const defaultPage = 1;

document.addEventListener("alpine:init", () => {
  Alpine.data("productList", () => ({
    loading: false,
    csvLoading: false,
    products: {} as GroupedProducts,

    /** Total number of elements corresponding to the current query. */
    nbPages: 0,

    isArchived: null as boolean,
    search: "",
    pageSize: defaultPageSize,
    page: defaultPage,

    async init() {
      const url = getCurrentUrlParams();
      this.search = url.get("search") || "";
      this.isArchived = url.get("isArchived") ?? false;
      await this.load();
      for (const param of ["search", "isArchived"]) {
        this.$watch(param, () => {
          this.page = defaultPage;
        });
      }
      for (const param of ["search", "isArchived", "page"]) {
        this.$watch(param, async (value: string) => {
          updateQueryString(param, value, History.Replace);
          this.nbPages = 0;
          this.products = {};
          await this.load();
        });
      }
    },

    /**
     * Build the object containing the query parameters corresponding
     * to the current filters
     */
    getQueryParams(): ProductSearchProductsDetailedData {
      const search = this.search.length > 0 ? this.search : null;
      const archived = ["true", "false"].includes(this.isArchived)
        ? this.isArchived
        : undefined;
      return {
        query: {
          page: this.page,
          // biome-ignore lint/style/useNamingConvention: api is in snake_case
          page_size: this.pageSize,
          search: search,
          // biome-ignore lint/style/useNamingConvention: api is in snake_case
          is_archived: archived,
        },
      };
    },

    /**
     * Fetch the products corresponding to the current filters
     */
    async load() {
      this.loading = true;
      const options = this.getQueryParams();
      const resp = await productSearchProductsDetailed(options);
      this.nbPages = Math.ceil(resp.data.count / defaultPageSize);
      this.products = resp.data.results.reduce<GroupedProducts>((acc, curr) => {
        const key = curr.product_type?.name ?? gettext("Uncategorized");
        if (!(key in acc)) {
          acc[key] = [];
        }
        acc[key].push(curr);
        return acc;
      }, {});
      this.loading = false;
    },
  }));
});
