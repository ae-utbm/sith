import { inheritHtmlElement, registerComponent } from "#core:utils/web-components";

@registerComponent("nfc-input")
export class NfcInput extends inheritHtmlElement("input") {
  connectedCallback() {
    super.connectedCallback();

    /* Disable feature if browser is not supported or if not HTTPS */
    // biome-ignore lint/correctness/noUndeclaredVariables: browser API
    if (typeof NDEFReader === "undefined") {
      return;
    }

    const button = document.createElement("button");
    const logo = document.createElement("i");
    logo.classList.add("fa-brands", "fa-nfc-symbol");
    button.setAttribute("type", "button"); // Prevent form submission on click
    button.appendChild(logo);
    button.addEventListener("click", async () => {
      // biome-ignore lint/correctness/noUndeclaredVariables: browser API
      const ndef = new NDEFReader();
      await ndef.scan();
      ndef.addEventListener("readingerror", () => {
        window.alert(gettext("Unsupported NFC card"));
      });

      // biome-ignore lint/correctness/noUndeclaredVariables: browser API
      ndef.addEventListener("reading", (event: NDEFReadingEvent) => {
        this.node.value = event.serialNumber.replace(/:/g, "").toUpperCase();
        /* Auto submit form, we need another button to not trigger our previously defined click event */
        const submit = document.createElement("button");
        this.node.appendChild(submit);
        submit.click();
        submit.remove();
      });
    });
    this.appendChild(button);
  }
}
