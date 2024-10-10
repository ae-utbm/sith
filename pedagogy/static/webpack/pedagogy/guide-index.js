import { uvFetchUvList } from "#openapi";

const pageDefault = 1;
const pageSizeDefault = 100;

document.addEventListener("alpine:init", () => {
  Alpine.data("uv_search", () => ({
    uvs: {
      count: 0,
      next: null,
      previous: null,
      results: [],
    },
    loading: false,
    page: pageDefault,
    // biome-ignore lint/style/useNamingConvention: api is in snake_case
    page_size: pageSizeDefault,
    search: "",
    department: [],
    // biome-ignore lint/style/useNamingConvention: api is in snake_case
    credit_type: [],
    semester: [],
    // biome-ignore lint/style/useNamingConvention: api is in snake_case
    to_change: [],
    pushstate: History.PUSH,

    update: undefined,

    initializeArgs() {
      const url = new URLSearchParams(window.location.search);
      this.pushstate = History.REPLACE;

      this.page = Number.parseInt(url.get("page")) || pageDefault;
      this.page_size = Number.parseInt(url.get("page_size")) || pageSizeDefault;
      this.search = url.get("search") || "";
      this.department = url.getAll("department");
      this.credit_type = url.getAll("credit_type");
      /* The semester is easier to use on the backend as an enum (spring/autumn/both/none)
          and easier to use on the frontend as an array ([spring, autumn]).
          Thus there is some conversion involved when both communicate together */
      this.semester = url.has("semester") ? url.get("semester").split("_AND_") : [];

      this.update();
    },

    async init() {
      this.update = Alpine.debounce(async () => {
        /* Create the whole url before changing everything all at once */
        const first = this.to_change.shift();
        // biome-ignore lint/correctness/noUndeclaredVariables: defined in script.js
        let url = updateQueryString(first.param, first.value, History.NONE);
        for (const value of this.to_change) {
          // biome-ignore lint/correctness/noUndeclaredVariables: defined in script.js
          url = updateQueryString(value.param, value.value, History.NONE, url);
        }
        // biome-ignore lint/correctness/noUndeclaredVariables: defined in script.js
        updateQueryString(first.param, first.value, this.pushstate, url);
        await this.fetchData(); /* reload data on form change */
        this.to_change = [];
        this.pushstate = History.PUSH;
      }, 50);

      const searchParams = ["search", "department", "credit_type", "semester"];
      const paginationParams = ["page", "page_size"];

      for (const param of searchParams) {
        this.$watch(param, () => {
          if (this.pushstate !== History.PUSH) {
            /* This means that we are doing a mass param edit */
            return;
          }
          /* Reset pagination on search */
          this.page = pageDefault;
          this.page_size = pageSizeDefault;
        });
      }
      for (const param of searchParams.concat(paginationParams)) {
        this.$watch(param, (value) => {
          this.to_change.push({ param: param, value: value });
          this.update();
        });
      }
      window.addEventListener("popstate", () => {
        this.initializeArgs();
      });
      this.initializeArgs();
    },

    async fetchData() {
      this.loading = true;
      const args = {
        // biome-ignore lint/style/useNamingConvention: api is in snake_case
        page_size: this.page_size,
      };
      for (const [param, value] of new URL(
        window.location.href,
      ).searchParams.entries()) {
        // Deal with array type params
        if (["credit_type", "department", "semester"].includes(param)) {
          if (args[param] === undefined) {
            args[param] = [];
          }
          args[param].push(value);
        } else {
          args[param] = value;
        }
      }
      this.uvs = (
        await uvFetchUvList({
          query: args,
        })
      ).data;
      this.loading = false;
    },

    maxPage() {
      return Math.ceil(this.uvs.count / this.page_size);
    },
  }));
});
