import { etransactioninfoFetchEtransactionData } from "#openapi";

document.addEventListener("alpine:init", () => {
  Alpine.data("etransaction", (initialData, basketId: number) => ({
    data: initialData,
    isCbAvailable: Object.keys(initialData).length > 0,

    async fill() {
      this.isCbAvailable = false;
      const res = await etransactioninfoFetchEtransactionData({
        path: {
          // biome-ignore lint/style/useNamingConvention: api is in snake_case
          basket_id: basketId,
        },
      });
      if (res.response.ok) {
        this.data = res.data;
        this.isCbAvailable = true;
      }
    },
  }));
});
