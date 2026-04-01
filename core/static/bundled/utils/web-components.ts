/**
 * Class decorator to register components easily
 * It's a wrapper around window.customElements.define
 * What's nice about it is that you don't separate the component registration
 * and the class definition
 **/
export function registerComponent(name: string, options?: ElementDefinitionOptions) {
  return (component: CustomElementConstructor) => {
    try {
      window.customElements.define(name, component, options);
    } catch (e) {
      if (e instanceof DOMException) {
        console.warn(e.message);
        return;
      }
      throw e;
    }
  };
}

/**
 * Safari doesn't support inheriting from HTML tags on web components
 * The technique is to:
 *  create a new web component
 *  create the desired type inside
 *  move all attributes to the child component
 *  store is at as `node` inside the parent
 **/
export interface InheritedHtmlElement<K extends keyof HTMLElementTagNameMap>
  extends HTMLElement {
  readonly inheritedTagName: K;
  node: HTMLElementTagNameMap[K];
}

/**
 * Generator function that creates an InheritedHtmlElement compatible class
 *
 * ```js
 * class MyClass extends inheritHtmlElement("select") {
 *    // do whatever
 * }
 * ```
 **/
export function inheritHtmlElement<K extends keyof HTMLElementTagNameMap>(tagName: K) {
  return class InheritedHtmlElementImpl
    extends HTMLElement
    implements InheritedHtmlElement<K>
  {
    readonly inheritedTagName = tagName;
    node: HTMLElementTagNameMap[K];

    connectedCallback(autoAddNode?: boolean) {
      this.node = document.createElement(this.inheritedTagName);
      const attributes: Attr[] = []; // We need to make a copy to delete while iterating
      for (const attr of this.attributes) {
        if (attr.name in this.node) {
          attributes.push(attr);
        }
      }

      // We move compatible attributes to the child element
      // This avoids weird inconsistencies between attributes
      // when we manipulate the dom in the future
      // This is especially important when using attribute based reactivity
      for (const attr of attributes) {
        this.removeAttributeNode(attr);
        this.node.setAttributeNode(attr);
      }

      this.node.innerHTML = this.innerHTML;
      this.innerHTML = "";

      // Automatically add node to DOM if autoAddNode is true or unspecified
      if (autoAddNode === undefined || autoAddNode) {
        this.appendChild(this.node);
      }
    }
  };
}
