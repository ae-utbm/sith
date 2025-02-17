import { paginated } from "#core:utils/api";
import { HttpReader, ZipWriter } from "@zip.js/zip.js";
import { showSaveFilePicker } from "native-file-system-adapter";
import {
  type PicturesFetchPicturesData,
  type PictureSchema,
  picturesFetchPictures,
} from "#openapi";

interface PagePictureConfig {
  userId?: number;
  albumId?: number;
}

document.addEventListener("alpine:init", () => {
  Alpine.data("user_pictures", (config: PagePictureConfig) => ({
    isDownloading: false,
    loading: true,
    pictures: [] as PictureSchema[],
    albums: {} as Record<string, PictureSchema[]>,

    async init() {
      const query: PicturesFetchPicturesData["query"] = {};

      if (config.userId) {
        query.users_identified = [config.userId];
      } else {
        query.album_id = config.albumId;
      }
      this.pictures = await paginated(picturesFetchPictures, { query: query });

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

    async downloadZip() {
      this.isDownloading = true;
      const bar = this.$refs.progress;
      bar.value = 0;
      bar.max = this.pictures.length;

      const incrementProgressBar = (_total: number): undefined => {
        bar.value++;
        return undefined;
      };

      const fileHandle = await showSaveFilePicker({
        _preferPolyfill: false,
        suggestedName: interpolate(
          gettext("pictures.%(extension)s"),
          { extension: "zip" },
          true,
        ),
        excludeAcceptAllOption: false,
      });
      const zipWriter = new ZipWriter(await fileHandle.createWritable());

      await Promise.all(
        this.pictures.map((p: PictureSchema) => {
          const imgName = `${p.album}/IMG_${p.date.replace(/[:\-]/g, "_")}${p.name.slice(p.name.lastIndexOf("."))}`;
          return zipWriter.add(imgName, new HttpReader(p.full_size_url), {
            level: 9,
            lastModDate: new Date(p.date),
            onstart: incrementProgressBar,
          });
        }),
      );

      await zipWriter.close();
      this.isDownloading = false;
    },
  }));
});
