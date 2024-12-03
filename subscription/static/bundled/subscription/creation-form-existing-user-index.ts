document.addEventListener("alpine:init", () => {
  Alpine.data("existing_user_subscription_form", () => ({
    loading: false,
    profileFragment: "" as string,

    async init() {
      const userSelect = document.getElementById("id_member") as HTMLSelectElement;
      userSelect.addEventListener("change", async () => {
        await this.loadProfile(Number.parseInt(userSelect.value));
      });
      await this.loadProfile(Number.parseInt(userSelect.value));
    },

    async loadProfile(userId: number) {
      if (!Number.isInteger(userId)) {
        this.profileFragment = "";
        return;
      }
      this.loading = true;
      const response = await fetch(`/user/${userId}/mini/`);
      this.profileFragment = await response.text();
      this.loading = false;
    },
  }));
});
