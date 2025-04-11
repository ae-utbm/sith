import { etransactioninfoFetchEtransactionData } from "#openapi";

document.addEventListener("alpine:init", () => {
  Alpine.data("etransaction", (initialData) => ({
    data: initialData,
    isCbAvailable: Object.keys(initialData).length > 0,

    async fill() {
      this.isCbAvailable = false;
      const res = await etransactioninfoFetchEtransactionData();
      if (res.response.ok) {
        this.data = res.data;
        this.isCbAvailable = true;
      }
    },
  }));
});
