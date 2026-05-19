import sort from "@alpinejs/sort";
import Alpine from "alpinejs";
import { polyfillCountryFlagEmojis } from "country-flag-emoji-polyfill";
import htmx from "htmx.org";
import { limitedChoices } from "#core:alpine/limited-choices";
import { expireOldStorage } from "#core:core/localstorage";
import { default as navbar } from "#core:core/navbar";
import {
  type NotificationPlugin,
  notificationsPlugin as notifications,
} from "#core:utils/notifications";

/**
 * Alpine
 */
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

/**
 * Polyfill for country flags (used for language choice)
 */
polyfillCountryFlagEmojis();

/**
 * HTMX
 */
document.body.addEventListener("htmx:beforeRequest", (event: CustomEvent) => {
  event.detail.target.ariaBusy = true;
});

document.body.addEventListener("htmx:beforeSwap", (event: CustomEvent) => {
  event.detail.target.ariaBusy = null;
});

Object.assign(window, { htmx });

/**
 * navbar
 */
navbar();

/**
 * Script that clears the cache when the cache version changes
 */
expireOldStorage();
