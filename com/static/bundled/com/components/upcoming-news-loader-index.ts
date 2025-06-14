import { type NewsDateSchema, newsFetchNewsDates } from "#openapi";

interface ParsedNewsDateSchema extends Omit<NewsDateSchema, "start_date" | "end_date"> {
  // biome-ignore lint/style/useNamingConvention: api is snake_case
  start_date: Date;
  // biome-ignore lint/style/useNamingConvention: api is snake_case
  end_date: Date;
}

document.addEventListener("alpine:init", () => {
  Alpine.data("upcomingNewsLoader", (startDate: Date, locale: string) => ({
    startDate: startDate,
    currentPage: 1,
    pageSize: 6,
    hasNext: true,
    loading: false,
    newsDates: [] as NewsDateSchema[],
    dateFormat: new Intl.DateTimeFormat(locale, {
      dateStyle: "medium",
      timeStyle: "short",
    }),

    async loadMore() {
      this.loading = true;
      const response = await newsFetchNewsDates({
        query: {
          after: this.startDate.toISOString(),
          // biome-ignore lint/style/useNamingConvention: api is snake_case
          text_format: "html",
          page: this.currentPage,
          // biome-ignore lint/style/useNamingConvention: api is snake_case
          page_size: this.pageSize,
        },
      });
      if (response.response.status === 404) {
        this.hasNext = false;
      } else if (response.data.next === null) {
        this.newsDates.push(...response.data.results);
        this.hasNext = false;
      } else {
        this.newsDates.push(...response.data.results);
        this.currentPage += 1;
      }
      this.loading = false;
    },

    groupedDates(): Record<string, NewsDateSchema[]> {
      return this.newsDates
        .map(
          (date: NewsDateSchema): ParsedNewsDateSchema => ({
            ...date,
            // biome-ignore lint/style/useNamingConvention: api is snake_case
            start_date: new Date(date.start_date),
            // biome-ignore lint/style/useNamingConvention: api is snake_case
            end_date: new Date(date.end_date),
          }),
        )
        .reduce(
          (acc: Record<string, ParsedNewsDateSchema[]>, date: ParsedNewsDateSchema) => {
            const key = date.start_date.toDateString();
            if (!acc[key]) {
              acc[key] = [];
            }
            acc[key].push(date);
            return acc;
          },
          {},
        );
    },
  }));
});
