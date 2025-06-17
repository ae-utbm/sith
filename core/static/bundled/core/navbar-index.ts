import { exportToHtml } from "#core:utils/globals";

exportToHtml("showMenu", () => {
  const navbar = document.getElementById("navbar-content");
  const current = navbar.getAttribute("mobile-display");
  navbar.setAttribute("mobile-display", current === "hidden" ? "revealed" : "hidden");
});

document.addEventListener("alpine:init", () => {
  const menuItems = document.querySelectorAll(".navbar details[name='navbar'].menu");
  const isDesktop = () => {
    return window.innerWidth >= 500;
  };
  for (const item of menuItems) {
    item.addEventListener("mouseover", () => {
      if (isDesktop()) {
        item.setAttribute("open", "");
      }
    });
    item.addEventListener("mouseout", () => {
      if (isDesktop()) {
        item.removeAttribute("open");
      }
    });
    item.addEventListener("click", (event: MouseEvent) => {
      // Don't close when clicking on desktop mode
      if ((event.target as HTMLElement).nodeName !== "SUMMARY" || event.detail === 0) {
        return;
      }

      if (isDesktop()) {
        event.preventDefault();
      }
    });
  }
});
