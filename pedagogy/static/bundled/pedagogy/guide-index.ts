import { getCurrentUrlParams, updateQueryString } from "#core:utils/history";
import { type SimpleUeSchema, ueFetchUeList } from "#openapi";

const pageDefault = 1;
const pageSizeDefault = 100;

document.addEventListener("alpine:init", () => {
  Alpine.data("ue_search", () => ({
    ues: {
      count: 0,
      next: null as string | null,
      previous: null as string | null,
      results: [] as SimpleUeSchema[],
    },
    loading: false,
    page: pageDefault,
    // biome-ignore lint/style/useNamingConvention: api is in snake_case
    page_size: pageSizeDefault,
    search: "",
    hideClosedUes: true,
    department: [] as string[],
    // biome-ignore lint/style/useNamingConvention: api is in snake_case
    credit_type: [] as string[],
    semester: [] as string[],
    // biome-ignore lint/style/useNamingConvention: api is in snake_case
    to_change: [] as { param: string; value: string }[],

    // dummy implementation to make TS happy.
    // The real function is initialized in init
    update: () => {
      console.warn("Update not yet initialized");
    },

    initializeArgs() {
      const url = getCurrentUrlParams();
      this.page = Number.parseInt(url.get("page") || pageDefault.toString(), 10);
      this.page_size = Number.parseInt(
        url.get("page_size") || pageSizeDefault.toString(),
        10,
      );
      this.search = url.get("search") || "";
      this.hideClosedUes = url.get("hideClosed") || true;
      this.department = url.getAll("department");
      this.credit_type = url.getAll("credit_type");
      /* The semester is easier to use on the backend as an enum (spring/autumn/both/none)
          and easier to use on the frontend as an array ([spring, autumn]).
          Thus there is some conversion involved when both communicate together */
      this.semester = url.get("semester")?.split("_AND_") || [];

      this.update();
    },

    async init() {
      this.update = Alpine.debounce(async () => {
        /* Create the whole url before changing everything all at once */
        for (const val of this.to_change) {
          updateQueryString(val.param, val.value);
        }
        await this.fetchData(); /* reload data on form change */
        this.to_change = [];
      }, 50);

      const searchParams = [
        "search",
        "hideClosedUes",
        "department",
        "credit_type",
        "semester",
      ];
      const paginationParams = ["page", "page_size"];

      for (const param of searchParams) {
        this.$watch(param, () => {
          /* Reset pagination on search */
          this.page = pageDefault;
          this.page_size = pageSizeDefault;
        });
      }
      for (const param of searchParams.concat(paginationParams)) {
        this.$watch(param, (value: string) => {
          this.to_change.push({ param: param, value: value });
          this.update();
        });
      }
      this.initializeArgs();
    },

    async fetchData() {
      this.loading = true;

      const res = await ueFetchUeList({
        query: {
          // biome-ignore lint/style/useNamingConvention: api is in snake_case
          page_size: this.page_size,
          // biome-ignore lint/style/useNamingConvention: api is in snake_case
          credit_type: this.credit_type.length > 0 ? this.credit_type : undefined,
          semester: this.semester.length > 0 ? this.semester : undefined,
          // biome-ignore lint/style/useNamingConvention: api is snake_case
          is_open: this.hideClosedUes ? true : undefined,
          department: this.department.length > 0 ? this.department : undefined,
          search: this.search || undefined,
        },
      });
      if (res.data !== undefined) {
        this.ues = res.data;
      }
      this.loading = false;
    },

    maxPage() {
      return Math.ceil(this.ues.count / this.page_size);
    },
  }));
});
