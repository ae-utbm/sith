import { AlertMessage } from "#core:utils/alert-message.ts";
import { BasketItem } from "#counter:counter/basket.ts";
import type { CounterConfig, ErrorMessage } from "#counter:counter/types.ts";
import type { CounterProductSelect } from "./components/counter-product-select-index.ts";

document.addEventListener("alpine:init", () => {
  Alpine.data("counter", (config: CounterConfig) => ({
    basket: {} as Record<string, BasketItem>,
    customerBalance: config.customerBalance,
    codeField: null as CounterProductSelect | null,
    alertMessage: new AlertMessage({ defaultDuration: 2000 }),

    init() {
      // Fill the basket with the initial data
      for (const entry of config.formInitial) {
        if (entry.id !== undefined && entry.quantity !== undefined) {
          this.addToBasket(entry.id, entry.quantity);
          this.basket[entry.id].errors = entry.errors ?? [];
        }
      }

      this.codeField = this.$refs.codeField;
      this.codeField.widget.focus();

      // It's quite tricky to manually apply attributes to the management part
      // of a formset so we dynamically apply it here
      this.$refs.basketManagementForm
        .querySelector("#id_form-TOTAL_FORMS")
        .setAttribute(":value", "getBasketSize()");
    },

    removeFromBasket(id: string) {
      delete this.basket[id];
    },

    addToBasket(id: string, quantity: number): ErrorMessage {
      const item: BasketItem =
        this.basket[id] || new BasketItem(config.products[id], 0);

      const oldQty = item.quantity;
      item.quantity += quantity;

      if (item.quantity <= 0) {
        delete this.basket[id];
        return "";
      }

      this.basket[id] = item;

      if (this.sumBasket() > this.customerBalance) {
        item.quantity = oldQty;
        if (item.quantity === 0) {
          delete this.basket[id];
        }
        return gettext("Not enough money");
      }

      return "";
    },

    getBasketSize() {
      return Object.keys(this.basket).length;
    },

    sumBasket() {
      if (this.getBasketSize() === 0) {
        return 0;
      }
      const total = Object.values(this.basket).reduce(
        (acc: number, cur: BasketItem) => acc + cur.sum(),
        0,
      ) as number;
      return total;
    },

    addToBasketWithMessage(id: string, quantity: number) {
      const message = this.addToBasket(id, quantity);
      if (message.length > 0) {
        this.alertMessage.display(message, { success: false });
      }
    },

    onRefillingSuccess(event: CustomEvent) {
      if (event.type !== "htmx:after-request" || event.detail.failed) {
        return;
      }
      this.customerBalance += Number.parseFloat(
        (event.detail.target.querySelector("#id_amount") as HTMLInputElement).value,
      );
      document.getElementById("selling-accordion").setAttribute("open", "");
      this.codeField.widget.focus();
    },

    finish() {
      if (this.getBasketSize() === 0) {
        this.alertMessage.display(gettext("You can't send an empty basket."), {
          success: false,
        });
        return;
      }
      this.$refs.basketForm.submit();
    },

    cancel() {
      location.href = config.cancelUrl;
    },

    handleCode() {
      const [quantity, code] = this.codeField.getSelectedProduct() as [number, string];

      if (this.codeField.getOperationCodes().includes(code.toUpperCase())) {
        if (code === "ANN") {
          this.cancel();
        }
        if (code === "FIN") {
          this.finish();
        }
      } else {
        this.addToBasketWithMessage(code, quantity);
      }
      this.codeField.widget.clear();
      this.codeField.widget.focus();
    },
  }));
});
