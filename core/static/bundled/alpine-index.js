import { alpinePlugin as notificationPlugin } from "#core:utils/notifications";
import sort from "@alpinejs/sort";
import Alpine from "alpinejs";

Alpine.plugin(sort);
Alpine.magic("notifications", notificationPlugin);
window.Alpine = Alpine;

window.addEventListener("DOMContentLoaded", () => {
  Alpine.start();
});
