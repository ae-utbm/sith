import { paginated } from "#core:utils/api";
import {
  picturesDeletePicture,
  picturesFetchIdentifications,
  picturesFetchPictures,
  picturesIdentifyUsers,
  picturesModeratePicture,
  usersidentifiedDeleteRelation,
} from "#openapi";

/**
 * @typedef PictureIdentification
 * @property {number} id The actual id of the identification
 * @property {UserProfile} user The identified user
 */

/**
 * A container for a picture with the users identified on it
 * able to prefetch its data.
 */
class PictureWithIdentifications {
  identifications = null;
  imageLoading = false;
  identificationsLoading = false;

  /**
   * @param {Picture} picture
   */
  constructor(picture) {
    Object.assign(this, picture);
  }

  /**
   * @param {Picture} picture
   */
  static fromPicture(picture) {
    return new PictureWithIdentifications(picture);
  }

  /**
   * If not already done, fetch the users identified on this picture and
   * populate the identifications field
   * @param {?Object=} options
   * @return {Promise<void>}
   */
  async loadIdentifications(options) {
    if (this.identificationsLoading) {
      return; // The users are already being fetched.
    }
    if (!!this.identifications && !options?.forceReload) {
      // The users are already fetched
      // and the user does not want to force the reload
      return;
    }
    this.identificationsLoading = true;
    this.identifications = (
      await picturesFetchIdentifications({
        // biome-ignore lint/style/useNamingConvention: api is in snake_case
        path: { picture_id: this.id },
      })
    ).data;
    this.identificationsLoading = false;
  }

  /**
   * Preload the photo and the identifications
   * @return {Promise<void>}
   */
  async preload() {
    const img = new Image();
    img.src = this.compressed_url;
    if (!img.complete) {
      this.imageLoading = true;
      img.addEventListener("load", () => {
        this.imageLoading = false;
      });
    }
    await this.loadIdentifications();
  }
}

/**
 * @typedef ViewerConfig
 * @property {number} userId Id of the user to get the pictures from
 * @property {number} albumId Id of the album to displlay
 * @property {number} firstPictureId id of the first picture to load on the page
 * @property {bool} userIsSasAdmin if the user is sas admin
 **/

/**
 * Load user picture page with a nice download bar
 * @param {ViewerConfig} config
 **/
window.loadViewer = (config) => {
  document.addEventListener("alpine:init", () => {
    Alpine.data("picture_viewer", () => ({
      /**
       * All the pictures that can be displayed on this picture viewer
       * @type PictureWithIdentifications[]
       **/
      pictures: [],
      /**
       * The currently displayed picture
       * Default dummy data are pre-loaded to avoid javascript error
       * when loading the page at the beginning
       * @type PictureWithIdentifications
       **/
      currentPicture: {
        // biome-ignore lint/style/useNamingConvention: api is in snake_case
        is_moderated: true,
        id: null,
        name: "",
        // biome-ignore lint/style/useNamingConvention: api is in snake_case
        display_name: "",
        // biome-ignore lint/style/useNamingConvention: api is in snake_case
        compressed_url: "",
        // biome-ignore lint/style/useNamingConvention: api is in snake_case
        profile_url: "",
        // biome-ignore lint/style/useNamingConvention: api is in snake_case
        full_size_url: "",
        owner: "",
        date: new Date(),
        identifications: [],
      },
      /**
       * The picture which will be displayed next if the user press the "next" button
       * @type ?PictureWithIdentifications
       **/
      nextPicture: null,
      /**
       * The picture which will be displayed next if the user press the "previous" button
       * @type ?PictureWithIdentifications
       **/
      previousPicture: null,
      /**
       * The select2 component used to identify users
       **/
      selector: undefined,
      /**
       * true if the page is in a loading state, else false
       **/
      /**
       * Error message when a moderation operation fails
       * @type string
       **/
      moderationError: "",
      /**
       * Method of pushing new url to the browser history
       * Used by popstate event and always reset to it's default value when used
       * @type History
       **/
      pushstate: History.PUSH,

      async init() {
        this.pictures = (
          await paginated(picturesFetchPictures, {
            // biome-ignore lint/style/useNamingConvention: api is in snake_case
            query: { album_id: config.albumId },
          })
        ).map(PictureWithIdentifications.fromPicture);
        // biome-ignore lint/correctness/noUndeclaredVariables: Imported from sith-select2.js
        this.selector = sithSelect2({
          element: $(this.$refs.search),
          // biome-ignore lint/correctness/noUndeclaredVariables: Imported from sith-select2.js
          dataSource: remoteDataSource("/api/user/search", {
            excluded: () => [
              ...(this.currentPicture.identifications || []).map((i) => i.user.id),
            ],
            resultConverter: (obj) => new Object({ ...obj, text: obj.display_name }),
          }),
          pictureGetter: (user) => user.profile_pict,
        });
        this.currentPicture = this.pictures.find((i) => i.id === config.firstPictureId);
        this.$watch("currentPicture", (current, previous) => {
          if (current === previous) {
            /* Avoid recursive updates */
            return;
          }
          this.updatePicture();
        });
        window.addEventListener("popstate", async (event) => {
          if (!event.state || event.state.sasPictureId === undefined) {
            return;
          }
          this.pushstate = History.REPLACE;
          this.currentPicture = this.pictures.find(
            (i) => i.id === Number.parseInt(event.state.sasPictureId),
          );
        });
        this.pushstate = History.REPLACE; /* Avoid first url push */
        await this.updatePicture();
      },

      /**
       * Update the page.
       * Called when the `currentPicture` property changes.
       *
       * The url is modified without reloading the page,
       * and the previous picture, the next picture and
       * the list of identified users are updated.
       */
      async updatePicture() {
        const updateArgs = [
          { sasPictureId: this.currentPicture.id },
          "",
          `/sas/picture/${this.currentPicture.id}/`,
        ];
        if (this.pushstate === History.REPLACE) {
          window.history.replaceState(...updateArgs);
          this.pushstate = History.PUSH;
        } else {
          window.history.pushState(...updateArgs);
        }

        this.moderationError = "";
        const index = this.pictures.indexOf(this.currentPicture);
        this.previousPicture = this.pictures[index - 1] || null;
        this.nextPicture = this.pictures[index + 1] || null;
        await this.currentPicture.loadIdentifications();
        this.$refs.mainPicture?.addEventListener("load", () => {
          // once the current picture is loaded,
          // start preloading the next and previous pictures
          this.nextPicture?.preload();
          this.previousPicture?.preload();
        });
      },

      async moderatePicture() {
        const res = await picturesModeratePicture({
          // biome-ignore lint/style/useNamingConvention: api is in snake_case
          path: { picture_id: this.currentPicture.id },
        });
        if (res.error) {
          this.moderationError = `${gettext("Couldn't moderate picture")} : ${res.statusText}`;
          return;
        }
        this.currentPicture.is_moderated = true;
        this.currentPicture.askedForRemoval = false;
      },

      async deletePicture() {
        const res = await picturesDeletePicture({
          // biome-ignore lint/style/useNamingConvention: api is in snake_case
          path: { picture_id: this.currentPicture.id },
        });
        if (res.error) {
          this.moderationError = `${gettext("Couldn't delete picture")} : ${res.statusText}`;
          return;
        }
        this.pictures.splice(this.pictures.indexOf(this.currentPicture), 1);
        if (this.pictures.length === 0) {
          // The deleted picture was the only one in the list.
          // As the album is now empty, go back to the parent page
          document.location.href = config.albumUrl;
        }
        this.currentPicture = this.nextPicture || this.previousPicture;
      },

      /**
       * Send the identification request and update the list of identified users.
       */
      async submitIdentification() {
        await picturesIdentifyUsers({
          path: {
            // biome-ignore lint/style/useNamingConvention: api is in snake_case
            picture_id: this.currentPicture.id,
          },
          body: this.selector.val().map((i) => Number.parseInt(i)),
        });
        // refresh the identified users list
        await this.currentPicture.loadIdentifications({ forceReload: true });
        this.selector.empty().trigger("change");
      },

      /**
       * Check if an identification can be removed by the currently logged user
       * @param {PictureIdentification} identification
       * @return {boolean}
       */
      canBeRemoved(identification) {
        return config.userIsSasAdmin || identification.user.id === config.userId;
      },

      /**
       * Untag a user from the current picture
       * @param {PictureIdentification} identification
       */
      async removeIdentification(identification) {
        const res = await usersidentifiedDeleteRelation({
          // biome-ignore lint/style/useNamingConvention: api is in snake_case
          path: { relation_id: identification.id },
        });
        if (!res.error && Array.isArray(this.currentPicture.identifications)) {
          this.currentPicture.identifications =
            this.currentPicture.identifications.filter(
              (i) => i.id !== identification.id,
            );
        }
      },
    }));
  });
};
