import { paginated } from "#core:utils/api";
import {
  type PictureSchema,
  type PicturesFetchPicturesData,
  picturesFetchPictures,
} from "#openapi";

interface PagePictureConfig {
  userId: number;
}

document.addEventListener("alpine:init", () => {
  Alpine.data("user_pictures", (config: PagePictureConfig) => ({
    loading: true,
    pictures: [] as PictureSchema[],
    albums: {} as Record<string, PictureSchema[]>,

    async init() {
      this.pictures = await paginated(picturesFetchPictures, {
        query: {
          // biome-ignore lint/style/useNamingConvention: from python api
          users_identified: [config.userId],
        } as PicturesFetchPicturesData["query"],
      });

      this.albums = this.pictures.reduce(
        (acc: Record<string, PictureSchema[]>, picture: PictureSchema) => {
          if (!acc[picture.album]) {
            acc[picture.album] = [];
          }
          acc[picture.album].push(picture);
          return acc;
        },
        {},
      );
      this.loading = false;
    },
  }));
});
