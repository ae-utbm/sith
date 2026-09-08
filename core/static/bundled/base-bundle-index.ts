/**
 * File containing main functions and library re-exports
 * that should be accessible throughout the whole website.
 *
 * The idea is to group all that shared code into a single bundle,
 * for more efficient tree-shaking and gzip compression.
 */

// Must be loaded before Apline
import htmx from "htmx.org";
import "htmx.org/dist/ext/hx-alpine-compat.js";
import "htmx.org/dist/ext/hx-prompt.js";
import "htmx.org/dist/ext/hx-download.js";

import sort from "@alpinejs/sort";
import Alpine from "alpinejs";
import { polyfillCountryFlagEmojis } from "country-flag-emoji-polyfill";
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
htmx.registerExtension("aria-busy", {
  // biome-ignore lint/style/useNamingConvention: api's name
  htmx_before_request: (
    _: HTMLElement,
    detail: { ctx: { target: HTMLElement | undefined } },
  ) => {
    if (detail.ctx.target !== undefined) {
      (detail.ctx.target as HTMLElement).ariaBusy = "true";
    }
  },
  // biome-ignore lint/style/useNamingConvention: api's name
  htmx_after_swap: (
    _: HTMLElement,
    detail: { ctx: { target: HTMLElement | undefined } },
  ) => {
    if (detail.ctx.target !== undefined) {
      (detail.ctx.target as HTMLElement).ariaBusy = null;
    }
  },
});

htmx.config.transitions = true;

Object.assign(window, { htmx });

/**
 * navbar
 */
navbar();

/**
 * Script that clears the cache when the cache version changes
 */
expireOldStorage();
