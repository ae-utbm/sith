import sort from "@alpinejs/sort";
import Alpine from "alpinejs";
import { limitedChoices } from "#core:alpine/limited-choices.ts";
import { alpinePlugin as notificationPlugin } from "#core:utils/notifications.ts";

Alpine.plugin([sort, limitedChoices]);
Alpine.magic("notifications", notificationPlugin);
window.Alpine = Alpine;

window.addEventListener("DOMContentLoaded", () => {
  Alpine.start();
});
