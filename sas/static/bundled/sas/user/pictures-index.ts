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
      // Check the cache before hitting the API.
      const storageKey = "userPictures";
      const cacheContent: { userId: number; pictures: PictureSchema[] }[] = JSON.parse(
        sessionStorage.getItem(storageKey) || "[]",
      );
      const userPictures = cacheContent.find((obj) => obj.userId === config.userId);
      if (
        userPictures !== undefined &&
        userPictures.pictures.length === config.nbPictures
      ) {
        // The cached value is considered valid
        // if it contains the right amount of pictures.
        // This amount is known because it is given in the template.
        return userPictures.pictures;
      }
      const pictures = await paginated(picturesFetchPictures, {
        // biome-ignore lint/style/useNamingConvention: from python api
        query: { users_identified: [config.userId] },
      } as PicturesFetchPicturesData);

      cacheContent.push({ userId: config.userId, pictures: pictures });
      try {
        // cache only the pictures of the last 4 visited profiles
        sessionStorage.setItem(storageKey, JSON.stringify(cacheContent.slice(-4)));
      } catch {
        // an exception is raised if the localstorage is entirely filled.
        // To be as safe as possible, delete the cached pictures.
        // A cache hit is not worth the page breaking.
        sessionStorage.removeItem(storageKey);
      }
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
