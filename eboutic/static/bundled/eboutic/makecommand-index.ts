/**
 * @readonly
 * @enum {number}
 */
const BillingInfoReqState = {
  // biome-ignore lint/style/useNamingConvention: this feels more like an enum
  SUCCESS: 1,
  // biome-ignore lint/style/useNamingConvention: this feels more like an enum
  FAILURE: 2,
  // biome-ignore lint/style/useNamingConvention: this feels more like an enum
  SENDING: 3,
};

document.addEventListener("alpine:init", () => {
  Alpine.store("billing_inputs", {
    // biome-ignore lint/correctness/noUndeclaredVariables: defined in eboutic_makecommand.jinja
    data: etData,

    async fill() {
      const button = document.getElementById("bank-submit-button") as HTMLButtonElement;
      button.disabled = true;
      // biome-ignore lint/correctness/noUndeclaredVariables: defined in eboutic_makecommand.jinja
      const res = await fetch(etDataUrl);
      if (res.ok) {
        this.data = await res.json();
        button.disabled = false;
      }
    },
  });

  Alpine.data("billing_infos", () => ({
    /** @type {BillingInfoReqState | null} */
    reqState: null,

    async sendForm() {
      this.reqState = BillingInfoReqState.SENDING;
      const form = document.getElementById("billing_info_form");
      document.getElementById("bank-submit-button").disabled = true;
      const payload = Object.fromEntries(
        Array.from(form.querySelectorAll("input, select"))
          .filter((elem) => elem.type !== "submit" && elem.value)
          .map((elem) => [elem.name, elem.value]),
      );
      // biome-ignore lint/correctness/noUndeclaredVariables: defined in eboutic_makecommand.jinja
      const res = await fetch(billingInfoUrl, {
        method: "PUT",
        body: JSON.stringify(payload),
      });
      this.reqState = res.ok
        ? BillingInfoReqState.SUCCESS
        : BillingInfoReqState.FAILURE;
      if (res.status === 422) {
        const errors = (await res.json()).detail.flatMap((err) => err.loc);
        for (const elem of Array.from(form.querySelectorAll("input")).filter((elem) =>
          errors.includes(elem.name),
        )) {
          elem.setCustomValidity(gettext("Incorrect value"));
          elem.reportValidity();
          elem.oninput = () => elem.setCustomValidity("");
        }
      } else if (res.ok) {
        Alpine.store("billing_inputs").fill();
      }
    },

    getAlertColor() {
      if (this.reqState === BillingInfoReqState.SUCCESS) {
        return "green";
      }
      if (this.reqState === BillingInfoReqState.FAILURE) {
        return "red";
      }
      return "";
    },

    getAlertMessage() {
      if (this.reqState === BillingInfoReqState.SUCCESS) {
        // biome-ignore lint/correctness/noUndeclaredVariables: defined in eboutic_makecommand.jinja
        return billingInfoSuccessMessage;
      }
      if (this.reqState === BillingInfoReqState.FAILURE) {
        // biome-ignore lint/correctness/noUndeclaredVariables: defined in eboutic_makecommand.jinja
        return billingInfoFailureMessage;
      }
      return "";
    },
  }));
});
