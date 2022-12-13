document.addEventListener('alpine:init', () => {
    Alpine.store('bank_payment_enabled', false)

    Alpine.store('billing_inputs', {
        data: JSON.parse(et_data)["data"],

        async fill() {
            document.getElementById("bank-submit-button").disabled = true;
            const request = new Request(et_data_url, {
                method: "GET",
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                },
            });
            const res = await fetch(request);
            if (res.ok) {
                const json = await res.json();
                if (json["data"]) {
                    this.data = json["data"];
                }
                document.getElementById("bank-submit-button").disabled = false;
            }
        }
    })

    Alpine.data('billing_infos', () => ({
        errors: [],
        successful: false,
        url: billing_info_exist ? edit_billing_info_url : create_billing_info_url,

        async send_form() {
            const form = document.getElementById("billing_info_form");
            const submit_button = form.querySelector("input[type=submit]")
            submit_button.disabled = true;
            document.getElementById("bank-submit-button").disabled = true;
            this.successful = false

            let payload = {};
            for (const elem of form.querySelectorAll("input")) {
                if (elem.type === "text" && elem.value) {
                    payload[elem.name] = elem.value;
                }
            }
            const country = form.querySelector("select");
            if (country && country.value) {
                payload[country.name] = country.value;
            }
            const request = new Request(this.url, {
                method: "POST",
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken(),
                },
                body: JSON.stringify(payload),
            });
            const res = await fetch(request);
            const json = await res.json();
            if (json["errors"]) {
                this.errors = json["errors"];
            } else {
                this.errors = [];
                this.successful = true;
                this.url = edit_billing_info_url;
                Alpine.store("billing_inputs").fill();
            }
            submit_button.disabled = false;
        }
    }))
})


