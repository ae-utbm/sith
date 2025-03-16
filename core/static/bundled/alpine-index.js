import { limitedChoices } from "#core:alpine/limited-choices";
import sort from "@alpinejs/sort";
import Alpine from "alpinejs";

Alpine.plugin([sort, limitedChoices]);
window.Alpine = Alpine;

window.addEventListener("DOMContentLoaded", () => {
  Alpine.start();
});
