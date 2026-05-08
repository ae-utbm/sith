import { userFetchUser } from "#openapi";

Alpine.data("existing_user_subscription_form", () => ({
  loading: false,
  selectedUser: "",
  profileFragment: "",
  dateOfBirth: "",
  dateOfBirthHidden: true,

  async init() {
    this.$watch("selectedUser", async () => {
      await this.loadProfile(Number.parseInt(this.selectedUser, 10));
    });

    // Wait for web components to load
    await this.$nextTick();

    // Force to detect the initial value
    this.selectedUser = this.$refs.userSelect.widget.getValue();
  },

  async loadProfile(userId: number) {
    if (!Number.isInteger(userId)) {
      this.profileFragment = "";
      this.dateOfBirth = "";
      this.dateOfBirthHidden = true;
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
    this.dateOfBirth = userInfos.data.date_of_birth;
    this.dateOfBirthHidden = userInfos.data.date_of_birth !== null;
    this.loading = false;
  },
}));
