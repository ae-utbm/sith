import { paginated } from "#core:utils/api";
import {
  type PictureSchema,
  type PicturesFetchPicturesData,
  picturesFetchPictures,
} from "#openapi";

interface PagePictureConfig {
  userId: number;
  nbPictures?: number;
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
      const localStorageInvalidationKey = `user${config.userId}PicturesNumber`;
      const lastCachedNumber = localStorage.getItem(localStorageInvalidationKey);
      if (
        lastCachedNumber !== null &&
        Number.parseInt(lastCachedNumber) === config.nbPictures
      ) {
        return JSON.parse(localStorage.getItem(localStorageKey));
      }
      const pictures = await paginated(picturesFetchPictures, {
        // biome-ignore lint/style/useNamingConvention: from python api
        query: { users_identified: [config.userId] },
      } as PicturesFetchPicturesData);
      localStorage.setItem(localStorageInvalidationKey, config.nbPictures.toString());
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

    allPictures(): PictureSchema[] {
      return this.albums.flatMap((album: Album) => album.pictures);
    },
  }));
});
