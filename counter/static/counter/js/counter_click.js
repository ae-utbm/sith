document.addEventListener('alpine:init', () => {
    Alpine.data('counter', () => ({
        basket: basket,
        errors: [],

        sum_basket() {
            if (!this.basket || Object.keys(this.basket).length === 0) {
                return 0;
            }
            const total = Object.values(this.basket)
                .reduce((acc, cur) => acc + cur["qty"] * cur["price"], 0);
            return total / 100;
        },

        async handle_action(event) {
            const payload = $(event.target).serialize();
            let request = new Request(click_api_url, {
                method: "POST",
                body: payload,
                headers: {
                    'Accept': 'application/json',
                    'X-CSRFToken': csrf_token,
                }
            })
            const response = await fetch(request);
            const json = await response.json();
            this.basket = json["basket"]
            this.errors = json["errors"]
            $('form.code_form #code_field').val("").focus();
        }
    }))
})

$(function () {
    /* Autocompletion in the code field */
    const code_field = $("#code_field");

    let quantity = "";
    let search = "";
    code_field.autocomplete({
        select: function (event, ui) {
            event.preventDefault();
            code_field.val(quantity + ui.item.value);
        },
        focus: function (event, ui) {
            event.preventDefault();
            code_field.val(quantity + ui.item.value);
        },
        source: function (request, response) {
            // by the dark magic of JS, parseInt("123abc") === 123
            quantity = parseInt(request.term);
            search = request.term.slice(quantity.toString().length)
            let matcher = new RegExp($.ui.autocomplete.escapeRegex(search), "i");
            response($.grep(products_autocomplete, function (value) {
                value = value.tags;
                return matcher.test(value);
            }));
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