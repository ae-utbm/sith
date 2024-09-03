/**
 * @typedef PictureIdentification
 * @property {number} id The actual id of the identification
 * @property {UserProfile} user The identified user
 */


document.addEventListener("alpine:init", () => {
  Alpine.data("picture_viewer", () => ({
    /**
     * All the pictures that can be displayed on this picture viewer
     * @type Picture[]
     * */
    pictures: [],
    /**
     * The users identified on the currently displayed picture
     * @type PictureIdentification[]
     */
    identifications: [],
    /**
     * The currently displayed picture
     * @type Picture
     * */
    current_picture: undefined,
    /**
     * The picture which will be displayed next if the user press the "next" button
     * @type ?Picture
     * */
    next_picture: null,
    /**
     * The picture which will be dispalyed next if the user press the "previous" button
     * @type ?Picture
     * */
    previous_picture: null,
    /**
     * The select2 component used to identify users
     */
    selector: undefined,
    /**
     * true if the page is in a loading state, else false
     */
    loading: true,
    /**
     * Error message when a moderation operation fails
     * @type string
     */
    moderation_error: "",

    async init() {
      this.pictures = await fetch_paginated(picture_endpoint);
      this.selector = sithSelect2({
        element: $(this.$refs.search),
        data_source: remote_data_source("/api/user/search", {
          excluded: () => [...this.identifications.map((i) => i.user.id)],
          result_converter: (obj) => Object({ ...obj, text: obj.display_name }),
        }),
        picture_getter: (user) => user.profile_pict,
      });
      this.current_picture = this.pictures.find(
        (i) => i.id === first_picture_id,
      );
      this.$watch("current_picture", () => this.update_picture());
      await this.update_picture();
    },

    /**
     * Update the page.
     * Called when the `current_picture` property changes.
     *
     * The url is modified without reloading the page,
     * and the previous picture, the next picture and
     * the list of identified users are updated.
     */
    async update_picture() {
      this.loading = true;
      window.history.pushState(
        {},
        "",
        `/sas/picture/${this.current_picture.id}/`,
      );
      this.moderation_error = "";
      const index = this.pictures.indexOf(this.current_picture);
      this.previous_picture = this.pictures[index - 1] || null;
      this.next_picture = this.pictures[index + 1] || null;
      this.identifications = await (
        await fetch(`/api/sas/picture/${this.current_picture.id}/identified`)
      ).json();
      this.loading = false;
    },

    async moderate_picture() {
      const res = await fetch(
        `/api/sas/picture/${this.current_picture.id}/moderate`,
        {
          method: "PATCH",
        },
      );
      if (!res.ok) {
        this.moderation_error =
          gettext("Couldn't moderate picture") + " : " + res.statusText;
        return;
      }
      this.current_picture.is_moderated = true;
      this.current_picture.asked_for_removal = false;
    },

    async delete_picture() {
      const res = await fetch(`/api/sas/picture/${this.current_picture}/`, {
        method: "DELETE",
      });
      if (!res.ok) {
        this.moderation_error =
          gettext("Couldn't delete picture") + " : " + res.statusText;
        return;
      }
      this.pictures.splice(this.pictures.indexOf(this.current_picture), 1);
      if (this.pictures.length === 0) {
        // The deleted picture was the only one in the list.
        // As the album is now empty, go back to the parent page
        document.location.href = album_url;
      }
      this.current_picture = this.next_picture || this.previous_picture;
    },

    /**
     * Send the identification request and update the list of identified users.
     */
    async submit_identification() {
      this.loading = true;
      const url = `/api/sas/picture/${this.current_picture.id}/identified`;
      await fetch(url, {
        method: "PUT",
        body: JSON.stringify(this.selector.val().map((i) => parseInt(i))),
      });
      // refresh the identified users list
      this.identifications = await (await fetch(url)).json();
      this.selector.empty().trigger("change");
      this.loading = false;
    },

    /**
     * Check if an identification can be removed by the currently logged user
     * @param {PictureIdentification} identification
     * @return {boolean}
     */
    can_be_removed(identification) {
      return user_is_sas_admin || identification.user.id === user_id;
    },

    /**
     * Untag a user from the current picture
     * @param {PictureIdentification} identification
     */
    async remove_identification(identification) {
      this.loading = true;
      const res = await fetch(`/api/sas/relation/${identification.id}`, {
        method: "DELETE",
      });
      if (res.ok) {
        this.identifications = this.identifications.filter(
          (i) => i.id !== identification.id,
        );
      }
      this.loading = false;
    },
  }));
});
