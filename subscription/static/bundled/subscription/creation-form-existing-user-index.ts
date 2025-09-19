import { userFetchUser } from "#openapi";

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
      const birthdayInput = document.getElementById("id_birthdate") as HTMLInputElement;
      if (!Number.isInteger(userId)) {
        this.profileFragment = "";
        birthdayInput.hidden = true;
        return;
      }
      this.loading = true;
      const [miniProfile, userInfos] = await Promise.all([
        fetch(`/user/${userId}/mini/`),
        // biome-ignore lint/style/useNamingConvention: api is snake_case
        userFetchUser({ path: { user_id: userId } }),
      ]);
      this.profileFragment = await miniProfile.text();
      // If the user has no birthdate yet, show the form input
      // to fill this info.
      // Else keep the input hidden and change its value to the user birthdate
      birthdayInput.value = userInfos.data.date_of_birth;
      birthdayInput.hidden = userInfos.data.date_of_birth !== null;
      this.loading = false;
    },
  }));
});
