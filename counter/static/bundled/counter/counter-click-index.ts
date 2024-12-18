import { exportToHtml } from "#core:utils/globals";
import type TomSelect from "tom-select";

interface CounterConfig {
  csrfToken: string;
  clickApiUrl: string;
  sessionBasket: Record<number, BasketItem>;
  customerBalance: number;
  customerId: number;
}
interface BasketItem {
  // biome-ignore lint/style/useNamingConvention: talking with python
  bonus_qty: number;
  price: number;
  qty: number;
}

exportToHtml("loadCounter", (config: CounterConfig) => {
  document.addEventListener("alpine:init", () => {
    Alpine.data("counter", () => ({
      basket: config.sessionBasket,
      errors: [],
      customerBalance: config.customerBalance,
      codeField: undefined,

      init() {
        this.codeField = this.$refs.codeField;
        this.codeField.widget.focus();
      },

      sumBasket() {
        if (!this.basket || Object.keys(this.basket).length === 0) {
          return 0;
        }
        const total = Object.values(this.basket).reduce(
          (acc: number, cur: BasketItem) => acc + cur.qty * cur.price,
          0,
        ) as number;
        return total / 100;
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

      async handleCode(event: SubmitEvent) {
        const widget: TomSelect = this.codeField.widget;
        const code = (widget.getValue() as string).toUpperCase();
        if (this.codeField.getOperationCodes().includes(code)) {
          $(event.target).submit();
        } else {
          await this.handleAction(event);
        }
        widget.clear();
        widget.focus();
      },

      async handleAction(event: SubmitEvent) {
        const payload = $(event.target).serialize();
        const request = new Request(config.clickApiUrl, {
          method: "POST",
          body: payload,
          headers: {
            // biome-ignore lint/style/useNamingConvention: this goes into http headers
            Accept: "application/json",
            "X-CSRFToken": config.csrfToken,
          },
        });
        const response = await fetch(request);
        const json = await response.json();
        this.basket = json.basket;
        this.errors = json.errors;
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
