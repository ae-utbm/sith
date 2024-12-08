import htmx from "htmx.org";

document.body.addEventListener("htmx:beforeRequest", (event) => {
  event.target.ariaBusy = true;
});

document.body.addEventListener("htmx:afterRequest", (event) => {
  event.originalTarget.ariaBusy = null;
});

Object.assign(window, { htmx });
