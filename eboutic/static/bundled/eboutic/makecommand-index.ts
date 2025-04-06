import { exportToHtml } from "#core:utils/globals";
import {
  type BillingInfoSchema,
  etransactioninfoFetchEtransactionData,
  etransactioninfoPutUserBillingInfo,
} from "#openapi";

enum BillingInfoReqState {
  Success = "0",
  Failure = "1",
  Sending = "2",
}

exportToHtml("BillingInfoReqState", BillingInfoReqState);

document.addEventListener("alpine:init", () => {
  Alpine.data("etransactionData", (initialData) => ({
    data: initialData,

    async fill() {
      const button = document.getElementById("bank-submit-button") as HTMLButtonElement;
      button.disabled = true;
      const res = await etransactioninfoFetchEtransactionData();
      if (res.response.ok) {
        this.data = res.data;
        button.disabled = false;
      }
    },
  }));

  Alpine.data("billing_infos", (userId: number) => ({
    /** @type {BillingInfoReqState | null} */
    reqState: null,

    async sendForm() {
      this.reqState = BillingInfoReqState.Sending;
      const form = document.getElementById("billing_info_form");
      const submitButton = document.getElementById(
        "bank-submit-button",
      ) as HTMLButtonElement;
      submitButton.disabled = true;
      const payload = Object.fromEntries(
        Array.from(form.querySelectorAll("input, select"))
          .filter((elem: HTMLInputElement) => elem.type !== "submit" && elem.value)
          .map((elem: HTMLInputElement) => [elem.name, elem.value]),
      );
      const res = await etransactioninfoPutUserBillingInfo({
        // biome-ignore lint/style/useNamingConvention: API is snake_case
        path: { user_id: userId },
        body: payload as unknown as BillingInfoSchema,
      });
      this.reqState = res.response.ok
        ? BillingInfoReqState.Success
        : BillingInfoReqState.Failure;
      if (res.response.status === 422) {
        const errors = await res.response
          .json()
          .detail.flatMap((err: Record<"loc", string>) => err.loc);
        for (const elem of Array.from(form.querySelectorAll("input")).filter((elem) =>
          errors.includes(elem.name),
        )) {
          elem.setCustomValidity(gettext("Incorrect value"));
          elem.reportValidity();
          elem.oninput = () => elem.setCustomValidity("");
        }
      } else if (res.response.ok) {
        this.$dispatch("billing-infos-filled");
      }
    },

    getAlertColor() {
      if (this.reqState === BillingInfoReqState.Success) {
        return "green";
      }
      if (this.reqState === BillingInfoReqState.Failure) {
        return "red";
      }
      return "";
    },

    getAlertMessage() {
      if (this.reqState === BillingInfoReqState.Success) {
        return gettext("Billing info registration success");
      }
      if (this.reqState === BillingInfoReqState.Failure) {
        return gettext("Billing info registration failure");
      }
      return "";
    },
  }));
});
