document.addEventListener("alpine:init", () => {
  Alpine.data("counter", () => ({
    // biome-ignore lint/correctness/noUndeclaredVariables: defined in counter_click.jinja
    basket: sessionBasket,
    errors: [],

    sumBasket() {
      if (!this.basket || Object.keys(this.basket).length === 0) {
        return 0;
      }
      const total = Object.values(this.basket).reduce(
        (acc, cur) => acc + cur.qty * cur.price,
        0,
      );
      return total / 100;
    },

    async handleCode(event) {
      const code = $(event.target).find("#code_field").val().toUpperCase();
      if (["FIN", "ANN"].includes(code)) {
        $(event.target).submit();
      } else {
        await this.handleAction(event);
      }
    },

    async handleAction(event) {
      const payload = $(event.target).serialize();
      // biome-ignore lint/correctness/noUndeclaredVariables: defined in counter_click.jinja
      const request = new Request(clickApiUrl, {
        method: "POST",
        body: payload,
        headers: {
          // biome-ignore lint/style/useNamingConvention: this goes into http headers
          Accept: "application/json",
          // biome-ignore lint/correctness/noUndeclaredVariables: defined in counter_click.jinja
          "X-CSRFToken": csrfToken,
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

$(() => {
  /* Autocompletion in the code field */
  const codeField = $("#code_field");

  let quantity = "";
  codeField.autocomplete({
    select: (event, ui) => {
      event.preventDefault();
      codeField.val(quantity + ui.item.value);
    },
    focus: (event, ui) => {
      event.preventDefault();
      codeField.val(quantity + ui.item.value);
    },
    source: (request, response) => {
      // biome-ignore lint/performance/useTopLevelRegex: performance impact is minimal
      const res = /^(\d+x)?(.*)/i.exec(request.term);
      quantity = res[1] || "";
      const search = res[2];
      const matcher = new RegExp($.ui.autocomplete.escapeRegex(search), "i");
      response(
        // biome-ignore lint/correctness/noUndeclaredVariables: defined in counter_click.jinja
        $.grep(productsAutocomplete, (value) => {
          return matcher.test(value.tags);
        }),
      );
    },
  });

  /* Accordion UI between basket and refills */
  $("#click_form").accordion({
    heightStyle: "content",
    activate: () => $(".focus").focus(),
  });
  $("#products").tabs();

  codeField.focus();
});
