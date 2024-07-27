/**
 * @readonly
 * @enum {number}
 */
const BillingInfoReqState = {
    SUCCESS: 1,
    FAILURE: 2
};


document.addEventListener("alpine:init", () => {
    Alpine.store("bank_payment_enabled", false)

    Alpine.store("billing_inputs", {
        data: et_data,

        async fill() {
            document.getElementById("bank-submit-button").disabled = true;
            const res = await fetch(et_data_url);
            if (res.ok) {
                this.data = await res.json();
                document.getElementById("bank-submit-button").disabled = false;
            }
        }
    })

    Alpine.data("billing_infos", () => ({
        /** @type {BillingInfoReqState | null} */
        req_state: null,

        async send_form() {
            const form = document.getElementById("billing_info_form");
            const submit_button = form.querySelector("input[type=submit]")
            submit_button.disabled = true;
            document.getElementById("bank-submit-button").disabled = true;
            this.req_state = null;

            let payload = form.querySelectorAll("input")
                .values()
                .filter((elem) => elem.type === "text" && elem.value)
                .reduce((acc, curr) => acc[curr.name] = curr.value, {});
            const country = form.querySelector("select");
            if (country && country.value) {
                payload[country.name] = country.value;
            }
            const res = await fetch(billing_info_url, {
                method: "PUT",
                body: JSON.stringify(payload),
            });
            this.req_state = res.ok ? BillingInfoReqState.SUCCESS : BillingInfoReqState.FAILURE;
            if (res.ok) {
                Alpine.store("billing_inputs").fill();
            }
            submit_button.disabled = false;
        },

        get_alert_color() {
            if (this.req_state === BillingInfoReqState.SUCCESS) {
                return "green";
            }
            if (this.req_state === BillingInfoReqState.FAILURE) {
                return "red";
            }
            return "";
        },

        get_alert_message() {
            if (this.req_state === BillingInfoReqState.SUCCESS) {
                return billing_info_success_message;
            }
            if (this.req_state === BillingInfoReqState.FAILURE) {
                return billing_info_failure_message;
            }
            return "";
        }
    }))
})


