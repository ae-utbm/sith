document.addEventListener("alpine:init", () => {
	Alpine.data("counter", () => ({
		basket,
		errors: [],

		sum_basket() {
			if (!this.basket || Object.keys(this.basket).length === 0) {
				return 0;
			}
			const total = Object.values(this.basket).reduce(
				(acc, cur) => acc + cur.qty * cur.price,
				0,
			);
			return total / 100;
		},

		async handle_code(event) {
			const code = $(event.target).find("#code_field").val().toUpperCase();
			if (["FIN", "ANN"].includes(code)) {
				$(event.target).submit();
			} else {
				await this.handle_action(event);
			}
		},

		async handle_action(event) {
			const payload = $(event.target).serialize();
			const request = new Request(click_api_url, {
				method: "POST",
				body: payload,
				headers: {
					Accept: "application/json",
					"X-CSRFToken": csrf_token,
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
	const code_field = $("#code_field");

	let quantity = "";
	code_field.autocomplete({
		select: (event, ui) => {
			event.preventDefault();
			code_field.val(quantity + ui.item.value);
		},
		focus: (event, ui) => {
			event.preventDefault();
			code_field.val(quantity + ui.item.value);
		},
		source: (request, response) => {
			const res = /^(\d+x)?(.*)/i.exec(request.term);
			quantity = res[1] || "";
			const search = res[2];
			const matcher = new RegExp($.ui.autocomplete.escapeRegex(search), "i");
			response(
				$.grep(products_autocomplete, (value) => {
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

	code_field.focus();
});
