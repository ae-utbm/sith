import { morph } from "@alpinejs/morph";
import sort from "@alpinejs/sort";
import Alpine from "alpinejs";

Alpine.plugin([sort, morph]);
window.Alpine = Alpine;

window.addEventListener("DOMContentLoaded", () => {
  Alpine.start();
});
