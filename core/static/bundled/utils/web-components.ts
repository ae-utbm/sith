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
        // biome-ignore lint/suspicious/noConsole: it's handy to troobleshot
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
 *  pass all attributes to the child component
 *  store is at as `node` inside the parent
 *
 * Since we can't use the generic type to instantiate the node, we create a generator function
 *
 * ```js
 * class MyClass extends inheritHtmlElement("select") {
 *    // do whatever
 * }
 * ```
 **/
export function inheritHtmlElement<K extends keyof HTMLElementTagNameMap>(tagName: K) {
  return class Inherited extends HTMLElement {
    protected node: HTMLElementTagNameMap[K];

    connectedCallback(autoAddNode?: boolean) {
      this.node = document.createElement(tagName);
      const attributes: Attr[] = []; // We need to make a copy to delete while iterating
      for (const attr of this.attributes) {
        if (attr.name in this.node) {
          attributes.push(attr);
        }
      }

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
