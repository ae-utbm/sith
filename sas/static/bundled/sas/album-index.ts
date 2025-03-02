import { paginated } from "#core:utils/api";
import { History, initialUrlParams, updateQueryString } from "#core:utils/history";
import {
  type PictureSchema,
  type PicturesFetchPicturesData,
  picturesFetchPictures,
} from "#openapi";

interface AlbumConfig {
  albumId: number;
  maxPageSize: number;
}

document.addEventListener("alpine:init", () => {
  Alpine.data("pictures", (config: AlbumConfig) => ({
    pictures: [] as PictureSchema[],
    page: Number.parseInt(initialUrlParams.get("page")) || 1,
    pushstate: History.Push /* Used to avoid pushing a state on a back action */,
    loading: false,

    async init() {
      await this.fetchPictures();
      this.$watch("page", () => {
        updateQueryString("page", this.page === 1 ? null : this.page, this.pushstate);
        this.pushstate = History.Push;
      });

      window.addEventListener("popstate", () => {
        this.pushstate = History.Replace;
        this.page =
          Number.parseInt(new URLSearchParams(window.location.search).get("page")) || 1;
      });
      this.config = config;
    },

    getPage(page: number) {
      return this.pictures.slice(
        (page - 1) * config.maxPageSize,
        config.maxPageSize * page,
      );
    },

    async fetchPictures() {
      this.loading = true;
      this.pictures = await paginated(picturesFetchPictures, {
        query: {
          // biome-ignore lint/style/useNamingConvention: API is in snake_case
          album_id: config.albumId,
        } as PicturesFetchPicturesData["query"],
      });
      this.loading = false;
    },

    nbPages() {
      return Math.ceil(this.pictures.length / config.maxPageSize);
    },
  }));
});
