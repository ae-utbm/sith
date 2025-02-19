import { exportToHtml } from "#core:utils/globals";
import { newsDeleteNews, newsFetchNewsDates, newsModerateNews } from "#openapi";

// This will be used in jinja templates,
// so we cannot use real enums as those are purely an abstraction of Typescript
const AlertState = {
  // biome-ignore lint/style/useNamingConvention: this feels more like an enum
  PENDING: 1,
  // biome-ignore lint/style/useNamingConvention: this feels more like an enum
  MODERATED: 2,
  // biome-ignore lint/style/useNamingConvention: this feels more like an enum
  DELETED: 3,
};
exportToHtml("AlertState", AlertState);

document.addEventListener("alpine:init", () => {
  Alpine.data("moderationAlert", (newsId: number) => ({
    state: AlertState.PENDING,
    newsId: newsId as number,
    loading: false,

    async moderateNews() {
      this.loading = true;
      // biome-ignore lint/style/useNamingConvention: api is snake case
      await newsModerateNews({ path: { news_id: this.newsId } });
      this.state = AlertState.MODERATED;
      this.$dispatch("news-moderated", { newsId: this.newsId, state: this.state });
      this.loading = false;
    },

    async deleteNews() {
      this.loading = true;
      // biome-ignore lint/style/useNamingConvention: api is snake case
      await newsDeleteNews({ path: { news_id: this.newsId } });
      this.state = AlertState.DELETED;
      this.$dispatch("news-moderated", { newsId: this.newsId, state: this.state });
      this.loading = false;
    },

    /**
     * Event receiver for when news dates are moderated.
     *
     * If the moderated date is linked to the same news
     * as the one this moderation alert is attached to,
     * then set the alert state to the same as the moderated one.
     */
    dispatchModeration(event: CustomEvent) {
      if (event.detail.newsId === this.newsId) {
        this.state = event.detail.state;
      }
    },

    /**
     * Query the server to know the number of news dates that would be moderated
     * if this one is moderated.
     */
    async nbModerated() {
      // What we want here is the count attribute of the response.
      // We don't care about the actual results,
      // so we ask for the minimum page size possible.
      const response = await newsFetchNewsDates({
        // biome-ignore lint/style/useNamingConvention: api is snake-case
        query: { news_id: this.newsId, page: 1, page_size: 1 },
      });
      return response.data.count;
    },
  }));
});
