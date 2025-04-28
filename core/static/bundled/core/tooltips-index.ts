import {
  type Placement,
  autoPlacement,
  computePosition,
  flip,
  offset,
  size,
} from "@floating-ui/dom";

/**
 * Library usage:
 *
 * Add a `tooltip` attribute to any html element with it's tooltip text
 * You can control the position of the tooltp with the `tooltip-position` attribute
 * Allowed placements are `auto`, `top`, `right`, `bottom`, `left`
 * You can add `-start` and `-end` to all allowed placement values except for `auto`
 * Default placement is `auto`
 * Note: placement are suggestions and the position could change if the popup gets
 *       outside of the screen.
 *
 * You can customize your tooltip by passing additionnal classes or ids to it
 * You can use `tooltip-class` and `tooltip-id` to add additional elements to the
 * `class` and `id` attribute of the generated tooltip
 *
 * @example
 * ```html
 * <p tooltip="tooltip text"></p>
 * <p tooltip="tooltip left" tooltip-position="left"></p>
 * <div tooltip="tooltip custom class" tooltip-class="custom custom-class"></div>
 * ```
 **/

type Status = "open" | "close";

const tooltips = new Map();

function getPosition(element: HTMLElement): Placement | "auto" {
  const position = element.getAttribute("tooltip-position");
  if (position) {
    return position as Placement | "auto";
  }
  return "auto";
}

function getMiddleware(element: HTMLElement) {
  const middleware = [offset(6), size()];
  if (getPosition(element) === "auto") {
    middleware.push(autoPlacement());
  } else {
    middleware.push(flip());
  }
  return { middleware: middleware };
}

function getPlacement(element: HTMLElement) {
  const position = getPosition(element);
  if (position !== "auto") {
    return { placement: position };
  }
  return {};
}

function createTooltip(element: HTMLElement) {
  const tooltip = document.createElement("div");
  document.body.append(tooltip);
  tooltips.set(element, tooltip);
  return tooltip;
}

function updateTooltip(element: HTMLElement, tooltip: HTMLElement, status: Status) {
  // Update tooltip status and set it's attributes and content
  tooltip.setAttribute("tooltip-status", status);
  tooltip.innerText = element.getAttribute("tooltip");

  for (const attributes of [
    { src: "tooltip-class", dst: "class", default: ["tooltip"] },
    { src: "tooltip-id", dst: "id", default: [] },
  ]) {
    const populated = attributes.default;
    if (element.hasAttribute(attributes.src)) {
      populated.push(...element.getAttribute(attributes.src).split(" "));
    }
    tooltip.setAttribute(attributes.dst, populated.join(" "));
  }
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
  updateTooltip(target, tooltip, "open");

  computePosition(target, tooltip, {
    ...getPlacement(target),
    ...getMiddleware(target),
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

  updateTooltip(target, getTooltip(target), "close");
});
