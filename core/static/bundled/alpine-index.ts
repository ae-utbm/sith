import sort from "@alpinejs/sort";
import { Alpine } from "alpinejs";
import { limitedChoices } from "#core:alpine/limited-choices";
import {
  type NotificationPlugin,
  notificationsPlugin as notifications,
} from "#core:utils/notifications";

declare module "alpinejs" {
  interface Magics<T> {
    $notifications: NotificationPlugin;
  }
}

Alpine.plugin([sort, limitedChoices, notifications]);
// biome-ignore lint/style/useNamingConvention: it's how it's named
Object.assign(window, { Alpine });

window.addEventListener("DOMContentLoaded", () => {
  Alpine.start();
});
