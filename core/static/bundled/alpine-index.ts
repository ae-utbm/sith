import sort from "@alpinejs/sort";
import { Alpine } from "alpinejs";
import { limitedChoices } from "#core:alpine/limited-choices";
import {
  type NotificationPlugin,
  alpinePlugin as notificationPlugin,
} from "#core:utils/notifications";

declare module "alpinejs" {
  interface Magics<T> {
    $notifications: NotificationPlugin;
  }
}
Alpine.plugin([sort, limitedChoices]);
Alpine.magic("notifications", notificationPlugin);
// biome-ignore lint/style/useNamingConvention: it's how it's named
Object.assign(window, { Alpine });

window.addEventListener("DOMContentLoaded", () => {
  Alpine.start();
});
