import {
  type InheritedHtmlElement,
  inheritHtmlElement,
  registerComponent,
} from "#core:utils/web-components.ts";

/**
 * ElementOnce web components
 *
 * Those elements ensures that their content is always included only once on a document
 * They are compatible with elements that are not managed with our Web Components
 **/
export interface ElementOnce<K extends keyof HTMLElementTagNameMap>
  extends InheritedHtmlElement<K> {
  getElementQuerySelector(): string;
  refresh(): void;
}

/**
 * Create an abstract class for ElementOnce types Web Components
 **/
export function elementOnce<K extends keyof HTMLElementTagNameMap>(tagName: K) {
  abstract class ElementOnceImpl
    extends inheritHtmlElement(tagName)
    implements ElementOnce<K>
  {
    abstract getElementQuerySelector(): string;

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
  }
  return ElementOnceImpl;
}

// Set of ElementOnce type components to refresh with the observer
const registeredComponents: Set<string> = new Set();

/**
 * Helper to register ElementOnce types Web Components
 * It's a wrapper around registerComponent that registers that component on
 * a MutationObserver that activates a refresh on them when elements are removed
 *
 * You are not supposed to unregister an element
 **/
export function registerElementOnce(name: string, options?: ElementDefinitionOptions) {
  registeredComponents.add(name);
  return registerComponent(name, options);
}

// Refresh all ElementOnce components on the document based on the tag name of the removed element
const refreshElement = <
  T extends keyof HTMLElementTagNameMap,
  K extends keyof HTMLElementTagNameMap,
>(
  components: HTMLCollectionOf<ElementOnce<T>>,
  removedTagName: K,
) => {
  for (const element of components) {
    // We can't guess if an element is compatible before we get one
    // We exit the function completely if it's not compatible
    if (element.inheritedTagName.toUpperCase() !== removedTagName.toUpperCase()) {
      return;
    }

    element.refresh();
  }
};

// Since we need to pause the observer, we make an helper to start it with consistent arguments
const startObserver = (observer: MutationObserver) => {
  observer.observe(document, {
    // We want to also listen for elements contained in the header (eg: link)
    subtree: true,
    childList: true,
  });
};

// Refresh ElementOnce components when changes happens
const observer = new MutationObserver((mutations: MutationRecord[]) => {
  // To avoid infinite recursion, we need to pause the observer while manipulation nodes
  observer.disconnect();
  for (const mutation of mutations) {
    for (const node of mutation.removedNodes) {
      if (node.nodeType !== node.ELEMENT_NODE) {
        continue;
      }
      for (const registered of registeredComponents) {
        refreshElement(
          document.getElementsByTagName(registered) as HTMLCollectionOf<
            ElementOnce<"html"> // The specific tag doesn't really matter
          >,
          (node as HTMLElement).tagName as keyof HTMLElementTagNameMap,
        );
      }
    }
  }
  // We then resume the observer
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
