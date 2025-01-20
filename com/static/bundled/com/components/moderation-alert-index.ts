import { exportToHtml } from "#core:utils/globals";
import Alpine from "alpinejs";
import { newsDeleteNews, newsModerateNews } from "#openapi";

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
      this.loading = false;
    },

    async deleteNews() {
      this.loading = true;
      // biome-ignore lint/style/useNamingConvention: api is snake case
      await newsDeleteNews({ path: { news_id: this.newsId } });
      this.state = AlertState.DELETED;
      this.loading = false;
    },
  }));
});
