import { exportToHtml } from "#core:utils/globals";
import { customerGetCustomer } from "#openapi";

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

      async updateBalance() {
        this.customerBalance = (
          await customerGetCustomer({
            path: {
              // biome-ignore lint/style/useNamingConvention: api is in snake_case
              customer_id: config.customerId,
            },
          })
        ).data.amount;
      },

      async handleCode(event: SubmitEvent) {
        const code = (
          $(event.target).find("#code_field").val() as string
        ).toUpperCase();
        if (["FIN", "ANN"].includes(code)) {
          $(event.target).submit();
        } else {
          await this.handleAction(event);
        }
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
        $("form.code_form #code_field").val("").focus();
      },
    }));
  });
});

interface Product {
  value: string;
  label: string;
  tags: string;
}
declare global {
  const productsAutocomplete: Product[];
}

$(() => {
  /* Autocompletion in the code field */
  // biome-ignore lint/suspicious/noExplicitAny: dealing with legacy jquery
  const codeField: any = $("#code_field");

  let quantity = "";
  codeField.autocomplete({
    // biome-ignore lint/suspicious/noExplicitAny: dealing with legacy jquery
    select: (event: any, ui: any) => {
      event.preventDefault();
      codeField.val(quantity + ui.item.value);
    },
    // biome-ignore lint/suspicious/noExplicitAny: dealing with legacy jquery
    focus: (event: any, ui: any) => {
      event.preventDefault();
      codeField.val(quantity + ui.item.value);
    },
    // biome-ignore lint/suspicious/noExplicitAny: dealing with legacy jquery
    source: (request: any, response: any) => {
      // biome-ignore lint/performance/useTopLevelRegex: performance impact is minimal
      const res = /^(\d+x)?(.*)/i.exec(request.term);
      quantity = res[1] || "";
      const search = res[2];
      // biome-ignore lint/suspicious/noExplicitAny: dealing with legacy jquery
      const matcher = new RegExp(($ as any).ui.autocomplete.escapeRegex(search), "i");
      response(
        $.grep(productsAutocomplete, (value: Product) => {
          return matcher.test(value.tags);
        }),
      );
    },
  });

  /* Accordion UI between basket and refills */
  // biome-ignore lint/suspicious/noExplicitAny: dealing with legacy jquery
  ($("#click_form") as any).accordion({
    heightStyle: "content",
    activate: () => $(".focus").focus(),
  });
  // biome-ignore lint/suspicious/noExplicitAny: dealing with legacy jquery
  ($("#products") as any).tabs();

  codeField.focus();
});
