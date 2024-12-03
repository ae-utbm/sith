import { History, initialUrlParams, updateQueryString } from "#core:utils/history";
import { picturesFetchPictures } from "#openapi";

/**
 * @typedef AlbumConfig
 * @property {number} albumId id of the album to visualize
 * @property {number} maxPageSize maximum number of elements to show on a page
 **/

/**
 * Create a family graph of an user
 * @param {AlbumConfig} config
 **/
window.loadAlbum = (config) => {
  document.addEventListener("alpine:init", () => {
    Alpine.data("pictures", () => ({
      pictures: {},
      page: Number.parseInt(initialUrlParams.get("page")) || 1,
      pushstate: History.Push /* Used to avoid pushing a state on a back action */,
      loading: false,

      async init() {
        await this.fetchPictures();
        this.$watch("page", () => {
          updateQueryString("page", this.page === 1 ? null : this.page, this.pushstate);
          this.pushstate = History.Push;
          this.fetchPictures();
        });

        window.addEventListener("popstate", () => {
          this.pushstate = History.Replace;
          this.page =
            Number.parseInt(new URLSearchParams(window.location.search).get("page")) ||
            1;
        });
      },

      async fetchPictures() {
        this.loading = true;
        this.pictures = (
          await picturesFetchPictures({
            query: {
              // biome-ignore lint/style/useNamingConvention: API is in snake_case
              album_id: config.albumId,
              page: this.page,
              // biome-ignore lint/style/useNamingConvention: API is in snake_case
              page_size: config.maxPageSize,
            },
          })
        ).data;
        this.loading = false;
      },

      nbPages() {
        return Math.ceil(this.pictures.count / config.maxPageSize);
      },
    }));
  });
};
