import type TomSelect from "tom-select";
import type { UserAjaxSelect } from "#core:core/components/ajax-select-index";
import { paginated } from "#core:utils/api";
import { History } from "#core:utils/history";
import {
  type IdentifiedUserSchema,
  type ModerationRequestSchema,
  type PictureSchema,
  type PicturesFetchIdentificationsResponse,
  type PicturesFetchPicturesData,
  picturesDeletePicture,
  picturesFetchIdentifications,
  picturesFetchModerationRequests,
  picturesFetchPictures,
  picturesIdentifyUsers,
  picturesModeratePicture,
  picturesRotatePicture,
  type UserProfileSchema,
  usersidentifiedDeleteRelation,
} from "#openapi";

/**
 * A container for a picture with the users identified on it
 * able to prefetch its data.
 */
class PictureWithIdentifications {
  identifications: PicturesFetchIdentificationsResponse = null;
  imageLoading = false;
  identificationsLoading = false;
  moderationLoading = false;
  id: number;
  compressedUrl: string = "";
  thumbUrl: string = "";
  fullSizeUrl: string = "";
  moderationRequests: ModerationRequestSchema[] = null;

  constructor(picture: PictureSchema) {
    Object.assign(this, picture);
    this.compressedUrl = picture.compressed_url;
    this.thumbUrl = picture.thumb_url;
    this.fullSizeUrl = picture.full_size_url;
  }

  static fromPicture(picture: PictureSchema): PictureWithIdentifications {
    return new PictureWithIdentifications(picture);
  }

  rebuildUrls(date: Date) {
    const buildUrl = (url: string) => {
      const base = url.split("?", 1)[0];
      return `${base}?date=${date.getTime().toString()}`;
    };
    this.compressedUrl = buildUrl(this.compressedUrl);
    this.thumbUrl = buildUrl(this.thumbUrl);
    this.fullSizeUrl = buildUrl(this.fullSizeUrl);
  }

  /**
   * If not already done, fetch the users identified on this picture and
   * populate the identifications field
   */
  async loadIdentifications(options?: { forceReload: boolean }): Promise<void> {
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

  async loadModeration(options?: { forceReload: boolean }): Promise<void> {
    if (this.moderationLoading) {
      return; // The moderation requests are already being fetched.
    }
    if (!!this.moderationRequests && !options?.forceReload) {
      // The moderation requests are already fetched
      // and the user does not want to force the reload
      return;
    }
    this.moderationLoading = true;
    this.moderationRequests = (
      await picturesFetchModerationRequests({
        // biome-ignore lint/style/useNamingConvention: api is in snake_case
        path: { picture_id: this.id },
      })
    ).data;
    this.moderationLoading = false;
  }

  async rotate(direction: "left" | "right") {
    this.imageLoading = true;
    const res = await picturesRotatePicture({
      // biome-ignore lint/style/useNamingConvention: api is snake case
      path: { picture_id: this.id, direction: direction },
    });
    // urls returned by the api include a timestamp for cache busting
    this.fullSizeUrl = res.data.full_size_url;
    this.compressedUrl = res.data.compressed_url;
    this.thumbUrl = res.data.thumb_url;
    this.imageLoading = false;
  }

  /**
   * Preload the photo and the identifications
   */
  async preload(): Promise<void> {
    const img = new Image();
    img.src = this.compressedUrl;
    if (!img.complete) {
      this.imageLoading = true;
      img.addEventListener("load", () => {
        this.imageLoading = false;
      });
    }
    await this.loadIdentifications();
  }
}

interface ViewerConfig {
  /** Id of the user to get the pictures from */
  userId: number;
  /** Url of the current album */
  albumUrl: string;
  /** Id of the album to display */
  albumId: number;
  /** id of the first picture to load on the page */
  firstPictureId: number;
  /** if the user is sas admin */
  userCanModerate: boolean;
}

/**
 * Load user picture page with a nice download bar
 **/
document.addEventListener("alpine:init", () => {
  Alpine.data("picture_viewer", (config: ViewerConfig) => ({
    /**
     * All the pictures that can be displayed on this picture viewer
     **/
    pictures: [] as PictureWithIdentifications[],
    /**
     * The currently displayed picture
     * Default dummy data are pre-loaded to avoid javascript error
     * when loading the page at the beginning
     * @type PictureWithIdentifications
     **/
    currentPicture: {
      // biome-ignore lint/style/useNamingConvention: api is in snake_case
      is_moderated: true,
      id: null as number,
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
      // biome-ignore lint/style/useNamingConvention: api is in snake_case
      created_at: new Date(),
      identifications: [] as IdentifiedUserSchema[],
    },
    /**
     * The picture which will be displayed next if the user press the "next" button
     **/
    nextPicture: null as PictureWithIdentifications,
    /**
     * The picture which will be displayed next if the user press the "previous" button
     **/
    previousPicture: null as PictureWithIdentifications,
    /**
     * The select2 component used to identify users
     **/
    selector: undefined as UserAjaxSelect,
    /**
     * Error message when a moderation operation fails
     **/
    moderationError: "",
    /**
     * Method of pushing new url to the browser history
     * Used by popstate event and always reset to it's default value when used
     **/
    pushstate: History.Push,

    async init() {
      this.pictures = (
        await paginated(picturesFetchPictures, {
          // biome-ignore lint/style/useNamingConvention: api is in snake_case
          query: { album_id: config.albumId },
        } as PicturesFetchPicturesData)
      ).map(PictureWithIdentifications.fromPicture);
      this.selector = this.$refs.search;
      this.selector.setFilter((users: UserProfileSchema[]) => {
        const resp: UserProfileSchema[] = [];
        const ids = [
          ...(this.currentPicture.identifications || []).map(
            (i: IdentifiedUserSchema) => i.user.id,
          ),
        ];
        for (const user of users) {
          if (!ids.includes(user.id)) {
            resp.push(user);
          }
        }
        return resp;
      });
      this.currentPicture = this.pictures.find(
        (i: PictureSchema) => i.id === config.firstPictureId,
      );
      this.$watch(
        "currentPicture",
        (current: PictureSchema, previous: PictureSchema) => {
          if (current === previous) {
            /* Avoid recursive updates */
            return;
          }
          this.updatePicture();
        },
      );
      window.addEventListener("popstate", async (event) => {
        if (!event.state || event.state.sasPictureId === undefined) {
          return;
        }
        this.pushstate = History.Replace;
        this.currentPicture = this.pictures.find(
          (i: PictureSchema) => i.id === Number.parseInt(event.state.sasPictureId, 10),
        );
      });
      this.pushstate = History.Replace; /* Avoid first url push */
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
    async updatePicture(): Promise<void> {
      const updateArgs = {
        data: { sasPictureId: this.currentPicture.id },
        unused: "",
        url: this.currentPicture.sas_url,
      };
      if (this.pushstate === History.Replace) {
        window.history.replaceState(updateArgs.data, updateArgs.unused, updateArgs.url);
        this.pushstate = History.Push;
      } else {
        window.history.pushState(updateArgs.data, updateArgs.unused, updateArgs.url);
      }

      this.moderationError = "";
      const index: number = this.pictures.indexOf(this.currentPicture);
      this.previousPicture = this.pictures[index - 1] || null;
      this.nextPicture = this.pictures[index + 1] || null;
      this.$refs.mainPicture?.addEventListener("load", () => {
        // once the current picture is loaded,
        // start preloading the next and previous pictures
        this.nextPicture?.preload();
        this.previousPicture?.preload();
      });
      if (this.currentPicture.asked_for_removal && config.userCanModerate) {
        await Promise.all([
          this.currentPicture.loadIdentifications(),
          this.currentPicture.loadModeration(),
        ]);
      } else {
        await this.currentPicture.loadIdentifications();
      }
    },

    async moderatePicture() {
      const res = await picturesModeratePicture({
        // biome-ignore lint/style/useNamingConvention: api is in snake_case
        path: { picture_id: this.currentPicture.id },
      });
      if (res.error) {
        this.moderationError = `${gettext("Couldn't moderate picture")} : ${(res.error as { detail: string }).detail}`;
        return;
      }
      this.currentPicture.is_moderated = true;
      this.currentPicture.asked_for_removal = false;
    },

    async deletePicture() {
      const res = await picturesDeletePicture({
        // biome-ignore lint/style/useNamingConvention: api is in snake_case
        path: { picture_id: this.currentPicture.id },
      });
      if (res.error) {
        this.moderationError = `${gettext("Couldn't delete picture")} : ${(res.error as { detail: string }).detail}`;
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
    async submitIdentification(): Promise<void> {
      const widget: TomSelect = this.selector.widget;
      await picturesIdentifyUsers({
        // biome-ignore lint/style/useNamingConvention: api is in snake_case
        path: { picture_id: this.currentPicture.id },
        body: widget.items.map((i: string) => Number.parseInt(i, 10)),
      });
      // refresh the identified users list
      await this.currentPicture.loadIdentifications({ forceReload: true });

      // Clear selection and cache of retrieved user so they can be filtered again
      widget.clear(false);
      widget.clearOptions();
      widget.setTextboxValue("");
    },

    /**
     * Check if an identification can be removed by the currently logged user
     */
    canBeRemoved(identification: IdentifiedUserSchema): boolean {
      return config.userCanModerate || identification.user.id === config.userId;
    },

    /**
     * Untag a user from the current picture
     */
    async removeIdentification(identification: IdentifiedUserSchema): Promise<void> {
      const res = await usersidentifiedDeleteRelation({
        // biome-ignore lint/style/useNamingConvention: api is in snake_case
        path: { relation_id: identification.id },
      });
      if (!res.error && Array.isArray(this.currentPicture.identifications)) {
        this.currentPicture.identifications =
          this.currentPicture.identifications.filter(
            (i: IdentifiedUserSchema) => i.id !== identification.id,
          );
      }
    },
  }));
});
