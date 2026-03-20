import { History, updateQueryString } from "#core:utils/history";
import {
  type ClubProfileSchema,
  type ClubSearchClubData,
  clubSearchClubProfile,
  type Options,
} from "#openapi";

type ClubStatus = "active" | "inactive" | "both";
const PAGE_SIZE = 50;

document.addEventListener("alpine:init", () => {
  Alpine.data("clubList", () => ({
    clubName: "",
    clubStatus: "active" as ClubStatus,
    currentPage: 1,
    nbPages: 1,
    clubs: [] as ClubProfileSchema[],
    loading: false,

    async init() {
      const urlParams = new URLSearchParams(window.location.search);
      this.clubName = urlParams.get("clubName") || "";
      this.clubStatus = urlParams.get("clubStatus") || "active";
      this.currentPage = urlParams.get("currentPage") || 1;
      for (const param of ["clubName", "clubStatus", "currentPage"]) {
        this.$watch(param, async (value: number | string) => {
          updateQueryString(param, value.toString(), History.Replace);
          await this.loadClubs();
        });
      }
      await this.loadClubs();
    },
    async loadClubs() {
      this.loading = true;
      const searchParams: Options<ClubSearchClubData> = {
        query: { page: this.currentPage },
      };
      if (this.clubName) {
        searchParams.query.search = this.clubName;
      }
      if (this.clubStatus === "active") {
        searchParams.query.is_active = true;
      } else if (this.clubStatus === "inactive") {
        searchParams.query.is_active = false;
      }
      const res = await clubSearchClubProfile(searchParams);
      this.nbPages = Math.ceil(res.data.count / PAGE_SIZE);
      this.clubs = res.data.results;
      this.loading = false;
    },

    getParagraphs(s: string) {
      if (!s) {
        return [];
      }
      return s
        .split("\n")
        .map((s) => s.trim())
        .filter((s) => s !== "");
    },
  }));
});
