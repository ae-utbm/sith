import Alpine from "alpinejs";
import { producttypeReorder } from "#openapi";

document.addEventListener("alpine:init", () => {
  Alpine.data("productTypesList", () => ({
    loading: false,
    alertMessage: {
      open: false,
      success: true,
      content: "",
      timeout: null,
    },

    async reorder(itemId: number, newPosition: number) {
      // The sort plugin of Alpine doesn't manage dynamic lists with x-sort
      // (cf. https://github.com/alpinejs/alpine/discussions/4157).
      // There is an open PR that fixes this issue
      // (cf. https://github.com/alpinejs/alpine/pull/4361).
      // However, it hasn't been merged yet.
      // To overcome this, I get the list of DOM elements
      // And fetch the `x-sort:item` attribute, which value is
      // the id of the object in database.
      // Please make this a little bit cleaner when the fix has been merged
      // into the main Alpine repo.
      this.loading = true;
      const productTypes = this.$refs.productTypes
        .childNodes as NodeListOf<HTMLLIElement>;
      const getId = (elem: HTMLLIElement) =>
        Number.parseInt(elem.getAttribute("x-sort:item"));
      const query =
        newPosition === 0
          ? { above: getId(productTypes.item(1)) }
          : { below: getId(productTypes.item(newPosition - 1)) };
      const response = await producttypeReorder({
        // biome-ignore lint/style/useNamingConvention: api is snake_case
        path: { type_id: itemId },
        query: query,
      });
      this.openAlertMessage(response.response);
      this.loading = false;
    },

    openAlertMessage(response: Response) {
      if (response.ok) {
        this.alertMessage.success = true;
        this.alertMessage.content = gettext("Products types reordered!");
      } else {
        this.alertMessage.success = false;
        this.alertMessage.content = interpolate(
          gettext("Product type reorganisation failed with status code : %d"),
          [response.status],
        );
      }
      this.alertMessage.open = true;
      if (this.alertMessage.timeout !== null) {
        clearTimeout(this.alertMessage.timeout);
      }
      this.alertMessage.timeout = setTimeout(() => {
        this.alertMessage.open = false;
      }, 2000);
      this.loading = false;
    },
  }));
});
