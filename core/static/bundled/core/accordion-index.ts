const setMaxHeight = (element: HTMLDetailsElement) => {
  element.setAttribute("style", `max-height: ${element.scrollHeight}px`);
};

// Initialize max-height at load
window.addEventListener("DOMContentLoaded", () => {
  for (const el of document.querySelectorAll("details.accordion")) {
    setMaxHeight(el as HTMLDetailsElement);
  }
});

// Accordion opened
new MutationObserver((mutations: MutationRecord[]) => {
  for (const mutation of mutations) {
    const target = mutation.target as HTMLDetailsElement;
    if (target.tagName !== "DETAILS" || !target.classList.contains("accordion")) {
      continue;
    }
    setMaxHeight(target);
  }
}).observe(document.body, {
  attributes: true,
  attributeFilter: ["open"],
  subtree: true,
});
