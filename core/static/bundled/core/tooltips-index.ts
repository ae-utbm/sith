import { type Placement, computePosition } from "@floating-ui/dom";

/**
 * Library usage:
 * Add a `tooltip` attribute to any html element with it's tooltip text
 * You can control the position of the tooltp with the `position` attribute
 * Allowed placements are `top`, `right`, `bottom`, `left`
 * You can add `-start` and `-end` to all allowed placement values
 **/

const tooltips = new Map();

function getPlacement(element: HTMLElement): Placement {
  const position = element.getAttribute("position");
  if (position) {
    return position as Placement;
  }
  return "bottom";
}

function createTooltip(element: HTMLElement) {
  const tooltip = document.createElement("div");
  document.body.append(tooltip);
  tooltip.classList.add("tooltip");
  tooltip.innerText = element.getAttribute("tooltip");
  tooltips.set(element, tooltip);
  return tooltip;
}

function getTooltip(element: HTMLElement) {
  const tooltip = tooltips.get(element);
  if (tooltip === undefined) {
    return createTooltip(element);
  }

  return tooltip;
}

addEventListener("mouseover", (event: MouseEvent) => {
  const target = event.target as HTMLElement;
  if (!target.hasAttribute("tooltip")) {
    return;
  }

  const tooltip = getTooltip(target);
  tooltip.setAttribute("tooltip-status", "open");

  computePosition(target, tooltip, {
    placement: getPlacement(target),
  }).then(({ x, y }) => {
    Object.assign(tooltip.style, {
      left: `${x}px`,
      top: `${y}px`,
    });
  });

  document.body.append(tooltip);
});

addEventListener("mouseout", (event: MouseEvent) => {
  const target = event.target as HTMLElement;
  if (!target.hasAttribute("tooltip")) {
    return;
  }

  getTooltip(target).setAttribute("tooltip-status", "close");
});
