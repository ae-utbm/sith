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
	image_loading = false;
	identifications_loading = false;

	/**
	 * @param {Picture} picture
	 */
	constructor(picture) {
		Object.assign(this, picture);
	}

	/**
	 * @param {Picture} picture
	 */
	static from_picture(picture) {
		return new PictureWithIdentifications(picture);
	}

	/**
	 * If not already done, fetch the users identified on this picture and
	 * populate the identifications field
	 * @param {?Object=} options
	 * @return {Promise<void>}
	 */
	async load_identifications(options) {
		if (this.identifications_loading) {
			return; // The users are already being fetched.
		}
		if (!!this.identifications && !options?.force_reload) {
			// The users are already fetched
			// and the user does not want to force the reload
			return;
		}
		this.identifications_loading = true;
		const url = `/api/sas/picture/${this.id}/identified`;
		this.identifications = await (await fetch(url)).json();
		this.identifications_loading = false;
	}

	/**
	 * Preload the photo and the identifications
	 * @return {Promise<void>}
	 */
	async preload() {
		const img = new Image();
		img.src = this.compressed_url;
		if (!img.complete) {
			this.image_loading = true;
			img.addEventListener("load", () => {
				this.image_loading = false;
			});
		}
		await this.load_identifications();
	}
}

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
		current_picture: {
			is_moderated: true,
			id: null,
			name: "",
			display_name: "",
			compressed_url: "",
			profile_url: "",
			full_size_url: "",
			owner: "",
			date: new Date(),
			identifications: [],
		},
		/**
		 * The picture which will be displayed next if the user press the "next" button
		 * @type ?PictureWithIdentifications
		 **/
		next_picture: null,
		/**
		 * The picture which will be displayed next if the user press the "previous" button
		 * @type ?PictureWithIdentifications
		 **/
		previous_picture: null,
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
		moderation_error: "",
		/**
		 * Method of pushing new url to the browser history
		 * Used by popstate event and always reset to it's default value when used
		 * @type History
		 **/
		pushstate: History.PUSH,

		async init() {
			this.pictures = (await fetch_paginated(picture_endpoint)).map(
				PictureWithIdentifications.from_picture,
			);
			this.selector = sithSelect2({
				element: $(this.$refs.search),
				data_source: remote_data_source("/api/user/search", {
					excluded: () => [
						...(this.current_picture.identifications || []).map(
							(i) => i.user.id,
						),
					],
					result_converter: (obj) => Object({ ...obj, text: obj.display_name }),
				}),
				picture_getter: (user) => user.profile_pict,
			});
			this.current_picture = this.pictures.find(
				(i) => i.id === first_picture_id,
			);
			this.$watch("current_picture", (current, previous) => {
				if (current === previous) {
					/* Avoid recursive updates */
					return;
				}
				this.update_picture();
			});
			window.addEventListener("popstate", async (event) => {
				if (!event.state || event.state.sas_picture_id === undefined) {
					return;
				}
				this.pushstate = History.REPLACE;
				this.current_picture = this.pictures.find(
					(i) => i.id === Number.parseInt(event.state.sas_picture_id),
				);
			});
			this.pushstate = History.REPLACE; /* Avoid first url push */
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
			const update_args = [
				{ sas_picture_id: this.current_picture.id },
				"",
				`/sas/picture/${this.current_picture.id}/`,
			];
			if (this.pushstate === History.REPLACE) {
				window.history.replaceState(...update_args);
				this.pushstate = History.PUSH;
			} else {
				window.history.pushState(...update_args);
			}

			this.moderation_error = "";
			const index = this.pictures.indexOf(this.current_picture);
			this.previous_picture = this.pictures[index - 1] || null;
			this.next_picture = this.pictures[index + 1] || null;
			await this.current_picture.load_identifications();
			this.$refs.main_picture?.addEventListener("load", () => {
				// once the current picture is loaded,
				// start preloading the next and previous pictures
				this.next_picture?.preload();
				this.previous_picture?.preload();
			});
		},

		async moderate_picture() {
			const res = await fetch(
				`/api/sas/picture/${this.current_picture.id}/moderate`,
				{
					method: "PATCH",
				},
			);
			if (!res.ok) {
				this.moderation_error = `${gettext("Couldn't moderate picture")} : ${res.statusText}`;
				return;
			}
			this.current_picture.is_moderated = true;
			this.current_picture.asked_for_removal = false;
		},

		async delete_picture() {
			const res = await fetch(`/api/sas/picture/${this.current_picture.id}`, {
				method: "DELETE",
			});
			if (!res.ok) {
				this.moderation_error = `${gettext("Couldn't delete picture")} : ${res.statusText}`;
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
			const url = `/api/sas/picture/${this.current_picture.id}/identified`;
			await fetch(url, {
				method: "PUT",
				body: JSON.stringify(
					this.selector.val().map((i) => Number.parseInt(i)),
				),
			});
			// refresh the identified users list
			await this.current_picture.load_identifications({ force_reload: true });
			this.selector.empty().trigger("change");
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
			const res = await fetch(`/api/sas/relation/${identification.id}`, {
				method: "DELETE",
			});
			if (res.ok && Array.isArray(this.current_picture.identifications)) {
				this.current_picture.identifications =
					this.current_picture.identifications.filter(
						(i) => i.id !== identification.id,
					);
			}
		},
	}));
});
