import { paginated } from "#core:utils/api";
import { HttpReader, ZipWriter } from "@zip.js/zip.js";
import { showSaveFilePicker } from "native-file-system-adapter";
import { picturesFetchPictures } from "#openapi";

/**
 * @typedef UserProfile
 * @property {number} id
 * @property {string} first_name
 * @property {string} last_name
 * @property {string} nick_name
 * @property {string} display_name
 * @property {string} profile_url
 * @property {string} profile_pict
 */
/**
 * @typedef Picture
 * @property {number} id
 * @property {string} name
 * @property {number} size
 * @property {string} date
 * @property {UserProfile} owner
 * @property {string} full_size_url
 * @property {string} compressed_url
 * @property {string} thumb_url
 * @property {string} album
 * @property {boolean} is_moderated
 * @property {boolean} asked_for_removal
 */

/**
 * @typedef PicturePageConfig
 * @property {number} userId Id of the user to get the pictures from (optional if albumId defined)
 * @property {number} albumId Id of the album to get the pictures from (optinal if userId defined)
 **/

/**
 * Load user picture page with a nice download bar
 * @param {PicturePageConfig} config
 **/

interface PagePictureConfig {
  userId?: number;
  albumId?: number;
}

document.addEventListener("alpine:init", () => {
  Alpine.data("user_pictures", (config: PagePictureConfig) => ({
    isDownloading: false,
    loading: true,
    pictures: [],
    albums: {},

    async init() {
      const query: Record<string, number> = {};

      if (config.userId) {
        query.user_identified = config.userId;
      } else {
        query.album_id = config.albumId;
      }
      this.pictures = await paginated(picturesFetchPictures, { query: query });

      this.albums = this.pictures.reduce((acc, picture) => {
        if (!acc[picture.album]) {
          acc[picture.album] = [];
        }
        acc[picture.album].push(picture);
        return acc;
      }, {});
      this.loading = false;
    },

    async downloadZip() {
      this.isDownloading = true;
      const bar = this.$refs.progress;
      bar.value = 0;
      bar.max = this.pictures.length;

      const incrementProgressBar = () => {
        bar.value++;
      };

      const fileHandle = await showSaveFilePicker({
        _preferPolyfill: false,
        suggestedName: interpolate(
          gettext("pictures.%(extension)s"),
          { extension: "zip" },
          true,
        ),
        types: {},
        excludeAcceptAllOption: false,
      });
      const zipWriter = new ZipWriter(await fileHandle.createWritable());

      await Promise.all(
        this.pictures.map((p) => {
          const imgName = `${p.album}/IMG_${p.date.replaceAll(/[:\-]/g, "_")}${p.name.slice(p.name.lastIndexOf("."))}`;
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
