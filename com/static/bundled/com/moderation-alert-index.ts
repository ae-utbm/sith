import { exportToHtml } from "#core:utils/globals.ts";
import { newsDeleteNews, newsFetchNewsDates, newsPublishNews } from "#openapi";

// This will be used in jinja templates,
// so we cannot use real enums as those are purely an abstraction of Typescript
const AlertState = {
  // biome-ignore lint/style/useNamingConvention: this feels more like an enum
  PENDING: 1,
  // biome-ignore lint/style/useNamingConvention: this feels more like an enum
  PUBLISHED: 2,
  // biome-ignore lint/style/useNamingConvention: this feels more like an enum
  DELETED: 3,
  // biome-ignore lint/style/useNamingConvention: this feels more like an enum
  DISPLAYED: 4, // When published at page generation
};
exportToHtml("AlertState", AlertState);

document.addEventListener("alpine:init", () => {
  Alpine.data("moderationAlert", (newsId: number) => ({
    state: AlertState.PENDING,
    newsId: newsId as number,
    loading: false,

    async publishNews() {
      this.loading = true;
      // biome-ignore lint/style/useNamingConvention: api is snake case
      await newsPublishNews({ path: { news_id: this.newsId } });
      this.state = AlertState.PUBLISHED;
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
    async nbToPublish(): Promise<number> {
      // What we want here is the count attribute of the response.
      // We don't care about the actual results,
      // so we ask for the minimum page size possible.
      const response = await newsFetchNewsDates({
        // biome-ignore lint/style/useNamingConvention: api is snake-case
        query: { news_id: this.newsId, page: 1, page_size: 1 },
      });
      return response.data.count;
    },

    weeklyEventWarningMessage(nbEvents: number): string {
      return interpolate(
        gettext(
          "This event will take place every week for %s weeks. " +
            "If you publish or delete this event, " +
            "it will also be published (or deleted) for the following weeks.",
        ),
        [nbEvents],
      );
    },
  }));
});
