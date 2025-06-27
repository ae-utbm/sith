import htmx from "htmx.org";
import "htmx-ext-alpine-morph";

document.body.addEventListener("htmx:beforeRequest", (event) => {
  event.detail.target.ariaBusy = true;
});

document.body.addEventListener("htmx:beforeSwap", (event) => {
  event.detail.target.ariaBusy = null;
});

Object.assign(window, { htmx });
