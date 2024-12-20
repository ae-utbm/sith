import { exportToHtml } from "#core:utils/globals";

const quantityForTrayPrice = 6;

interface CounterConfig {
  csrfToken: string;
  clickApiUrl: string;
  customerBalance: number;
  customerId: number;
  products: Record<string, Product>;
}

interface Product {
  code: string;
  name: string;
  price: number;
  hasTrayPrice: boolean;
}

class BasketItem {
  quantity: number;
  product: Product;

  constructor(product: Product, quantity: number) {
    this.quantity = quantity;
    this.product = product;
  }

  getBonusQuantity(): number {
    if (!this.product.hasTrayPrice) {
      return 0;
    }
    return Math.floor(this.quantity / quantityForTrayPrice);
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
        this.codeField = this.$refs.codeField;
        this.codeField.widget.focus();
        // It's quite tricky to manually apply attributes to the management part
        // of a formset so we dynamically apply it here
        this.$refs.basketManagementForm
          .querySelector("#id_form-TOTAL_FORMS")
          .setAttribute(":value", "getBasketSize()");
      },

      getItemIdFromCode(code: string): string {
        return Object.keys(config.products).find(
          (key) => config.products[key].code === code,
        );
      },

      removeFromBasket(code: string) {
        delete this.basket[this.getItemIdFromCode(code)];
      },

      addToBasket(code: string, quantity: number): [boolean, string] {
        const id = this.getItemIdFromCode(code);
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
        this.$refs.basketForm.submit();
      },

      cancel() {
        this.basket = new Object({});
        // We need to wait for the templated form to be removed before sending
        this.$nextTick(() => {
          this.finish();
        });
      },

      handleCode(event: SubmitEvent) {
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
