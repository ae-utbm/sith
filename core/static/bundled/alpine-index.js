import sort from "@alpinejs/sort";
import Alpine from "alpinejs";

Alpine.plugin(sort);
window.Alpine = Alpine;

window.addEventListener("DOMContentLoaded", () => {
  Alpine.start();
});
