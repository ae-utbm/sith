import { alpinePlugin } from "#core:utils/notifications";
import sort from "@alpinejs/sort";
import Alpine from "alpinejs";

Alpine.plugin(sort);
Alpine.magic("notifications", alpinePlugin);
window.Alpine = Alpine;

window.addEventListener("DOMContentLoaded", () => {
  Alpine.start();
});
