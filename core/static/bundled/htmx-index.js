import htmx from "htmx.org";
import "htmx-ext-alpine-morph";

document.body.addEventListener("htmx:beforeRequest", (event) => {
  event.target.ariaBusy = true;
});

document.body.addEventListener("htmx:afterRequest", (event) => {
  event.originalTarget.ariaBusy = null;
});

Object.assign(window, { htmx });
