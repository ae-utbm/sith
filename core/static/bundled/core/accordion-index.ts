const updateMaxHeight = (element: HTMLDetailsElement) => {
  const content = element.querySelector(".accordion-content") as HTMLElement | null;
  if (!content) {
    return;
  }
  if (element.hasAttribute("open")) {
    content.style.maxHeight = `${content.scrollHeight}px`;
  } else {
    content.style.maxHeight = "0px";
  }
};

// Initialize max-height at load
window.addEventListener("DOMContentLoaded", () => {
  for (const el of document.querySelectorAll("details.accordion")) {
    updateMaxHeight(el as HTMLDetailsElement);
  }
});

// Accordion opened
new MutationObserver((mutations: MutationRecord[]) => {
  for (const mutation of mutations) {
    const target = mutation.target as HTMLDetailsElement;
    if (target.tagName !== "DETAILS" || !target.classList.contains("accordion")) {
      continue;
    }
    updateMaxHeight(target);
  }
}).observe(document.body, {
  attributes: true,
  attributeFilter: ["open"],
  subtree: true,
});
