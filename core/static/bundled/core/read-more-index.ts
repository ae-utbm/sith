import clip from "@arendjr/text-clipper";

/*
	This script adds a way to have a 'show more / show less' button
	on some text content.

	The usage is very simple, you just have to add the attribute `show-more`
	with the desired max size to the element you want to add the button to.
	This script does html matching and is able to properly cut rendered markdown.

	Example usage:
		<p show-more="20">
			My very long text will be cut by this script
		</p>
*/

function showMore(element: HTMLElement) {
  if (!element.hasAttribute("show-more")) {
    return;
  }

  // Mark element as loaded so we can hide unloaded
  // tags with css and avoid blinking text
  element.setAttribute("show-more-loaded", "");

  const fullContent = element.innerHTML;
  const clippedContent = clip(
    element.innerHTML,
    Number.parseInt(element.getAttribute("show-more") as string, 10),
    {
      html: true,
    },
  );

  // If already at the desired size, we don't do anything
  if (clippedContent === fullContent) {
    return;
  }

  const actionLink = document.createElement("a");
  actionLink.setAttribute("class", "show-more-link");

  let opened = false;

  const setText = () => {
    if (opened) {
      element.innerHTML = fullContent;
      actionLink.innerText = gettext("Show less");
    } else {
      element.innerHTML = clippedContent;
      actionLink.innerText = gettext("Show more");
    }
    element.appendChild(document.createElement("br"));
    element.appendChild(actionLink);
  };

  const toggle = () => {
    opened = !opened;
    setText();
  };

  setText();
  actionLink.addEventListener("click", (event) => {
    event.preventDefault();
    toggle();
  });
}

document.addEventListener("DOMContentLoaded", () => {
  for (const elem of document.querySelectorAll("[show-more]")) {
    showMore(elem as HTMLElement);
  }
});
