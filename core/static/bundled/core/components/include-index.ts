import { inheritHtmlElement, registerComponent } from "#core:utils/web-components.ts";

/**
 * Create an abstract class for ElementOnce types Web Components
 *
 * Those class aren't really abstract because that would be complicated with the
 * multiple inheritance involved
 * Instead, we just raise an unimplemented error
 **/
function elementOnce<K extends keyof HTMLElementTagNameMap>(tagName: K) {
  return class ElementOnce extends inheritHtmlElement(tagName) {
    getElementQuerySelector(): string {
      throw new Error("Unimplemented");
    }

    clearNode() {
      while (this.firstChild) {
        this.removeChild(this.lastChild);
      }
    }

    refresh() {
      this.clearNode();
      if (document.querySelectorAll(this.getElementQuerySelector()).length === 0) {
        this.appendChild(this.node);
      }
    }

    connectedCallback() {
      super.connectedCallback(false);
      this.refresh();
    }

    disconnectedCallback() {
      // The MutationObserver can't see web components being removed
      // It also can't see if something is removed inside after the component gets deleted
      // We need to manually clear the containing node to trigger the observer
      this.clearNode();
    }
  };
}

// Set of ElementOnce type components to refresh with the observer
const registeredComponents: Set<string> = new Set();

/**
 * Helper to register ElementOnce types Web Components
 * It's a wrapper around registerComponent that registers that component on
 * a MutationObserver that activates a refresh on them when elements are removed
 **/
function registerElementOnce(name: string, options?: ElementDefinitionOptions) {
  registeredComponents.add(name);
  return registerComponent(name, options);
}

const startObserver = (observer: MutationObserver) => {
  observer.observe(document, {
    // We want to also listen for elements contained in the header (eg: link)
    subtree: true,
    childList: true,
  });
};

// Refresh *-once components when changes happens
const observer = new MutationObserver((mutations: MutationRecord[]) => {
  observer.disconnect();
  for (const mutation of mutations) {
    for (const node of mutation.removedNodes) {
      if (node.nodeType !== node.ELEMENT_NODE) {
        continue;
      }
      const refreshElement = (componentName: string, tagName: string) => {
        for (const element of document.getElementsByTagName(componentName)) {
          // We can't guess if an element is compatible before we get one
          // We exit the function completely if it's not compatible
          if (
            (element as any).inheritedTagName.toUpperCase() !== tagName.toUpperCase()
          ) {
            return;
          }

          (element as any).refresh();
        }
      };
      for (const registered of registeredComponents) {
        refreshElement(registered, (node as HTMLElement).tagName);
      }
    }
  }
  startObserver(observer);
});

startObserver(observer);

/**
 * Web component used to import css files only once
 * If called multiple times or the file was already imported, it does nothing
 **/
@registerElementOnce("link-once")
export class LinkOnce extends elementOnce("link") {
  getElementQuerySelector(): string {
    // We get href from node.attributes instead of node.href to avoid getting the domain part
    return `link[href='${this.node.attributes.getNamedItem("href").nodeValue}']`;
  }
}

/**
 * Web component used to import javascript files only once
 * If called multiple times or the file was already imported, it does nothing
 **/
@registerElementOnce("script-once")
export class ScriptOnce extends inheritHtmlElement("script") {
  getElementQuerySelector(): string {
    // We get href from node.attributes instead of node.src to avoid getting the domain part
    return `script[src='${this.node.attributes.getNamedItem("src").nodeValue}']`;
  }
}
