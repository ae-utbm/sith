import { paginated } from "#core:utils/api";
import { History, initialUrlParams, updateQueryString } from "#core:utils/history";
import {
  type AlbumFetchAlbumData,
  type AlbumSchema,
  type PictureSchema,
  type PicturesFetchPicturesData,
  albumFetchAlbum,
  picturesFetchPictures,
} from "#openapi";

interface AlbumPicturesConfig {
  albumId: number;
  maxPageSize: number;
}

interface SubAlbumsConfig {
  parentId: number;
}

document.addEventListener("alpine:init", () => {
  Alpine.data("pictures", (config: AlbumPicturesConfig) => ({
    pictures: [] as PictureSchema[],
    page: Number.parseInt(initialUrlParams.get("page")) || 1,
    pushstate: History.Push /* Used to avoid pushing a state on a back action */,
    loading: false,
    config: config,

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
          Number.parseInt(new URLSearchParams(window.location.search).get("page")) || 1;
      });
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

  Alpine.data("albums", (config: SubAlbumsConfig) => ({
    albums: [] as AlbumSchema[],
    config: config,
    loading: false,

    async init() {
      await this.fetchAlbums();
    },

    async fetchAlbums() {
      this.loading = true;
      this.albums = await paginated(albumFetchAlbum, {
        // biome-ignore lint/style/useNamingConvention: API is snake_case
        query: { parent_id: this.config.parentId },
      } as AlbumFetchAlbumData);
      this.loading = false;
    },
  }));
});
