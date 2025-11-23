import { limitedChoices } from "#core:alpine/limited-choices";
import { alpinePlugin as notificationPlugin } from "#core:utils/notifications";
import { morph } from "@alpinejs/morph";
import sort from "@alpinejs/sort";
import Alpine from "alpinejs";

Alpine.plugin([sort, morph, limitedChoices]);
Alpine.magic("notifications", notificationPlugin);
window.Alpine = Alpine;

window.addEventListener("DOMContentLoaded", () => {
  Alpine.start();
});
