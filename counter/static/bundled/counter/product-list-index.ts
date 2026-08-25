import { showSaveFilePicker } from "native-file-system-adapter";
import type TomSelect from "tom-select";
import type { ClubAjaxSelect } from "#club:club/components/ajax-select-index";
import type { NestedKeyOf } from "#core:types/nested-key";
import { type PaginatedRequest, paginated } from "#core:utils/api";
import { csv } from "#core:utils/csv";
import { getCurrentUrlParams, History, updateQueryString } from "#core:utils/history";
import type {
  CounterAjaxSelect,
  ProductTypeAjaxSelect,
} from "#counter:counter/components/ajax-select-index";
import {
  type ProductSchema,
  type ProductSearchProductsDetailedData,
  productSearchProductsDetailed,
} from "#openapi";

type ProductType = string;
type GroupedProducts = Record<ProductType, ProductSchema[]>;

const defaultPageSize = 100;
const defaultPage = 1;

// biome-ignore lint/style/useNamingConvention: api is snake case
type ProductWithPriceSchema = ProductSchema & { selling_price: string };

/**
 * Keys of the properties to include in the CSV.
 */
const csvColumns = [
  "id",
  "name",
  "code",
  "description",
  "product_type.name",
  "club.name",
  "limit_age",
  "purchase_price",
  "selling_price",
  "archived",
] as NestedKeyOf<ProductWithPriceSchema>[];

/**
 * Title of the csv columns.
 */
const csvColumnTitles = [
  "id",
  gettext("name"),
  "code",
  "description",
  gettext("product type"),
  "club",
  gettext("limit age"),
  gettext("purchase price"),
  gettext("selling price"),
  gettext("archived"),
];

type ProductStatus = "active" | "archived" | "both";

document.addEventListener("alpine:init", () => {
  Alpine.data("productList", () => ({
    loading: false,
    csvLoading: false,
    products: {} as GroupedProducts,

    /** Total number of elements corresponding to the current query. */
    nbPages: 0,
    productStatus: "" as ProductStatus,
    search: "",
    productTypes: [] as string[],
    clubs: [] as string[],
    counters: [] as string[],
    pageSize: defaultPageSize,
    page: defaultPage,

    async init() {
      const url = getCurrentUrlParams();
      this.search = url.get("search") || "";
      this.productStatus = (url.get("productStatus") ?? "active") as ProductStatus;
      const productTypesWidget = (this.$refs.productTypesInput as ProductTypeAjaxSelect)
        .widget as TomSelect;
      productTypesWidget.on("change", (items: string[]) => {
        this.productTypes = [...items];
      });
      const clubsWidget = (this.$refs.clubsInput as ClubAjaxSelect).widget as TomSelect;
      clubsWidget.on("change", (items: string[]) => {
        this.clubs = [...items];
      });
      const countersWidget = (this.$refs.countersInput as CounterAjaxSelect)
        .widget as TomSelect;
      countersWidget.on("change", (items: string[]) => {
        this.counters = [...items];
      });

      await this.load();
      const searchParams = [
        "search",
        "productStatus",
        "productTypes",
        "clubs",
        "counters",
      ];
      for (const param of searchParams) {
        this.$watch(param, () => {
          this.page = defaultPage;
        });
      }
      for (const param of [...searchParams, "page"]) {
        this.$watch(param, async (value: string) => {
          updateQueryString(param, value, History.Replace);
          this.nbPages = 0;
          await this.load();
        });
      }
    },

    /**
     * Build the object containing the query parameters corresponding
     * to the current filters
     */
    getQueryParams(): Omit<ProductSearchProductsDetailedData, "url"> {
      const search = this.search.length > 0 ? this.search : null;
      // If active or archived products must be filtered, put the filter in the request
      // Else, don't include the filter
      const isArchived = ["active", "archived"].includes(this.productStatus)
        ? this.productStatus === "archived"
        : undefined;
      return {
        query: {
          page: this.page,
          // biome-ignore lint/style/useNamingConvention: api is in snake_case
          page_size: this.pageSize,
          search: search,
          // biome-ignore lint/style/useNamingConvention: api is in snake_case
          is_archived: isArchived,
          // biome-ignore lint/style/useNamingConvention: api is in snake_case
          product_type: [...this.productTypes.map(Number.parseInt)],
          club: [...this.clubs.map(Number.parseInt)],
          counter: [...this.counters.map(Number.parseInt)],
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
      if (resp.data === undefined) {
        console.error("Product search request failed");
        return;
      }
      this.nbPages = Math.ceil(resp.data.count / defaultPageSize);
      this.products = resp.data.results.reduce<GroupedProducts>(
        (acc: GroupedProducts, curr: ProductSchema) => {
          const key = curr.product_type?.name ?? gettext("Uncategorized");
          if (!(key in acc)) {
            acc[key] = [];
          }
          acc[key].push(curr);
          return acc;
        },
        {},
      );
      this.loading = false;
    },

    /**
     * Download products corresponding to the current filters as a CSV file.
     * If the pagination has multiple pages, all pages are downloaded.
     */
    async downloadCsv() {
      this.csvLoading = true;
      const fileHandle = await showSaveFilePicker({
        _preferPolyfill: false,
        suggestedName: gettext("products.csv"),
        types: [],
        excludeAcceptAllOption: false,
      });
      // if products to download are already in-memory, directly take them.
      // If not, fetch them.
      const products: ProductSchema[] =
        this.nbPages > 1
          ? await paginated(
              productSearchProductsDetailed,
              this.getQueryParams() as PaginatedRequest,
            )
          : Object.values<ProductSchema[]>(this.products).flat();
      // CSV cannot represent nested data
      // so we create a row for each price of each product.
      const productsWithPrice: ProductWithPriceSchema[] = products.flatMap(
        (product: ProductSchema) =>
          product.prices.map((price) =>
            // biome-ignore lint/style/useNamingConvention: API is snake_case
            Object.assign(product, { selling_price: price.amount }),
          ),
      );
      const content = csv.stringify(productsWithPrice, {
        columns: csvColumns,
        titleRow: csvColumnTitles,
      });
      const file = await fileHandle.createWritable();
      await file.write(content);
      await file.close();
      this.csvLoading = false;
    },
  }));
});
