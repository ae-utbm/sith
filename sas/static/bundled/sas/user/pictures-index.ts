import { paginated } from "#core:utils/api";
import {
  type PictureSchema,
  type PicturesFetchPicturesData,
  picturesFetchPictures,
} from "#openapi";

interface PagePictureConfig {
  userId: number;
  lastPhotoDate?: string;
}

interface Album {
  id: number;
  name: string;
  pictures: PictureSchema[];
}

document.addEventListener("alpine:init", () => {
  Alpine.data("user_pictures", (config: PagePictureConfig) => ({
    loading: true,
    albums: [] as Album[],

    async fetchPictures(): Promise<PictureSchema[]> {
      const localStorageKey = `user${config.userId}Pictures`;
      const localStorageDateKey = `user${config.userId}PicturesDate`;
      const lastCachedDate = localStorage.getItem(localStorageDateKey);
      if (
        config.lastPhotoDate !== undefined &&
        lastCachedDate !== undefined &&
        lastCachedDate >= config.lastPhotoDate
      ) {
        return JSON.parse(localStorage.getItem(localStorageKey));
      }
      const pictures = await paginated(picturesFetchPictures, {
        // biome-ignore lint/style/useNamingConvention: from python api
        query: { users_identified: [config.userId] },
      } as PicturesFetchPicturesData);
      localStorage.setItem(localStorageDateKey, config.lastPhotoDate);
      localStorage.setItem(localStorageKey, JSON.stringify(pictures));
      return pictures;
    },

    async init() {
      const pictures = await this.fetchPictures();
      const groupedAlbums = Object.groupBy(pictures, (i: PictureSchema) => i.album.id);
      this.albums = Object.values(groupedAlbums).map((pictures: PictureSchema[]) => {
        return {
          id: pictures[0].album.id,
          name: pictures[0].album.name,
          pictures: pictures,
        };
      });
      this.albums.sort((a: Album, b: Album) => b.id - a.id);
      const hash = document.location.hash.replace("#", "");
      if (hash.startsWith("album-")) {
        this.$nextTick(() => document.getElementById(hash)?.scrollIntoView()).then();
      }
      this.loading = false;
    },
  }));
});
