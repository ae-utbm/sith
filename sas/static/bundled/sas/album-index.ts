import { paginated } from "#core:utils/api";
import { History, initialUrlParams, updateQueryString } from "#core:utils/history";
import {
  type AlbumFetchAlbumData,
  type AlbumSchema,
  type PictureSchema,
  type PicturesFetchPicturesData,
  type PicturesUploadPictureErrors,
  albumFetchAlbum,
  picturesFetchPictures,
  picturesUploadPicture,
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
        // biome-ignore lint/style/useNamingConvention: API is in snake_case
        query: { album_id: config.albumId },
      } as PicturesFetchPicturesData);
      this.loading = false;
    },

    nbPages() {
      return Math.ceil(this.pictures.length / config.maxPageSize);
    },
  }));

  Alpine.data("albums", (config: SubAlbumsConfig) => ({
    albums: [] as AlbumSchema[],
    loading: false,

    async init() {
      await this.fetchAlbums();
    },

    async fetchAlbums() {
      this.loading = true;
      this.albums = await paginated(albumFetchAlbum, {
        // biome-ignore lint/style/useNamingConvention: API is snake_case
        query: { parent_id: config.parentId },
      } as AlbumFetchAlbumData);
      this.loading = false;
    },
  }));

  Alpine.data("pictureUpload", (albumId: number) => ({
    errors: [] as string[],
    pictures: [],
    sending: false,
    progress: null as HTMLProgressElement,

    init() {
      this.progress = this.$refs.progress;
    },

    async sendPictures() {
      const input = this.$refs.pictures as HTMLInputElement;
      const files = input.files;
      this.errors = [];
      this.progress.value = 0;
      this.progress.max = files.length;
      this.sending = true;
      for (const file of files) {
        await this.sendPicture(file);
      }
      this.sending = false;
      // This should trigger a reload of the pictures of the `picture` Alpine data
      this.$dispatch("pictures-upload-done");
    },

    async sendPicture(file: File) {
      const res = await picturesUploadPicture({
        // biome-ignore lint/style/useNamingConvention: api is snake_case
        body: { album_id: albumId, picture: file },
      });
      if (!res.response.ok) {
        let msg = "";
        if (res.response.status === 422) {
          msg = (res.error as PicturesUploadPictureErrors[422]).detail
            .map((err: Record<"ctx", Record<"error", string>>) => err.ctx.error)
            .join(" ; ");
        } else {
          msg = Object.values(res.error.detail).join(" ; ");
        }
        this.errors.push(`${file.name} : ${msg}`);
      }
      this.progress.value += 1;
    },
  }));
});
