import { exportToHtml } from "#core:utils/globals";

interface InitialFormData {
  /* Used to refill the form when the backend raises an error */
  id?: Pick<Product, "id">;
  quantity?: number;
  errors?: string[];
}

interface CounterConfig {
  customerBalance: number;
  customerId: number;
  products: Record<string, Product>;
  formInitial: InitialFormData[];
  cancelUrl: string;
}

interface Product {
  id: string;
  code: string;
  name: string;
  price: number;
  hasTrayPrice: boolean;
  quantityForTrayPrice: number;
}

class BasketItem {
  quantity: number;
  product: Product;
  quantityForTrayPrice: number;
  errors: string[];

  constructor(product: Product, quantity: number) {
    this.quantity = quantity;
    this.product = product;
    this.errors = [];
  }

  getBonusQuantity(): number {
    if (!this.product.hasTrayPrice) {
      return 0;
    }
    return Math.floor(this.quantity / this.product.quantityForTrayPrice);
  }

  sum(): number {
    return (this.quantity - this.getBonusQuantity()) * this.product.price;
  }
}

exportToHtml("loadCounter", (config: CounterConfig) => {
  document.addEventListener("alpine:init", () => {
    Alpine.data("counter", () => ({
      basket: {} as Record<string, BasketItem>,
      errors: [],
      customerBalance: config.customerBalance,
      codeField: undefined,

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

      addToBasket(id: string, quantity: number): [boolean, string] {
        const item: BasketItem =
          this.basket[id] || new BasketItem(config.products[id], 0);

        const oldQty = item.quantity;
        item.quantity += quantity;

        if (item.quantity <= 0) {
          delete this.basket[id];
          return [true, ""];
        }

        if (item.sum() > this.customerBalance) {
          item.quantity = oldQty;
          return [false, gettext("Not enough money")];
        }

        this.basket[id] = item;
        return [true, ""];
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

      onRefillingSuccess(event: CustomEvent) {
        if (event.type !== "htmx:after-request" || event.detail.failed) {
          return;
        }
        this.customerBalance += Number.parseFloat(
          (event.detail.target.querySelector("#id_amount") as HTMLInputElement).value,
        );
        document.getElementById("selling-accordion").click();
        this.codeField.widget.focus();
      },

      finish() {
        if (this.getBasketSize() > 0) {
          this.$refs.basketForm.submit();
        }
      },

      cancel() {
        location.href = config.cancelUrl;
      },

      handleCode() {
        const [quantity, code] = this.codeField.getSelectedProduct() as [
          number,
          string,
        ];

        if (this.codeField.getOperationCodes().includes(code.toUpperCase())) {
          if (code === "ANN") {
            this.cancel();
          }
          if (code === "FIN") {
            this.finish();
          }
        } else {
          this.addToBasket(code, quantity);
        }
        this.codeField.widget.clear();
        this.codeField.widget.focus();
      },
    }));
  });
});

$(() => {
  /* Accordion UI between basket and refills */
  // biome-ignore lint/suspicious/noExplicitAny: dealing with legacy jquery
  ($("#click_form") as any).accordion({
    heightStyle: "content",
    activate: () => $(".focus").focus(),
  });
  // biome-ignore lint/suspicious/noExplicitAny: dealing with legacy jquery
  ($("#products") as any).tabs();
});
