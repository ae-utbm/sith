document.addEventListener("alpine:init", () => {
  Alpine.data("user_identification", () => ({
    identifications: [],
    selector: undefined,

    async init() {
      this.loading = true;
      this.identifications = await (
        await fetch(`/api/sas/picture/${picture_id}/identified`)
      ).json();
      this.selector = sithSelect2({
        element: $(this.$refs.search),
        data_source: remote_data_source("/api/user/search", {
          excluded: () => [...this.identifications.map((i) => i.user.id)],
          result_converter: (obj) => Object({ ...obj, text: obj.display_name }),
        }),
        picture_getter: (user) => user.profile_pict,
      });
      this.loading = false;
    },

    async submit_identification() {
      this.loading = true;
      const url = `/api/sas/picture/${picture_id}/identified`;
      await fetch(url, {
        method: "PUT",
        body: JSON.stringify(this.selector.val().map((i) => parseInt(i))),
      });
      // refresh the identified users list
      this.identifications = await (await fetch(url)).json();
      this.selector.empty().trigger("change");
      this.loading = false;
    },

    can_be_removed(item) {
      return user_is_sas_admin || item.user.id === user_id;
    },

    async remove(item) {
      this.loading = true;
      const res = await fetch(`/api/sas/relation/${item.id}`, {
        method: "DELETE",
      });
      if (res.ok) {
        this.identifications = this.identifications.filter(
          (i) => i.id !== item.id,
        );
      }
      this.loading = false;
    },
  }));
});
