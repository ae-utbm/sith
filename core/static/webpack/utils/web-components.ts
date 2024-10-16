/**
 * Safari doesn't support inheriting from HTML tags on web components
 * The technique is to:
 *  create a new web component
 *  create the desired type inside
 *  pass all attributes to the child component
 *  store is at as a widget inside the parent
 *
 * To use this, you must use the tag name twice, once for creating the class
 * and the second time while calling super to pass it to the constructor
 **/
export class InheritedComponent<
  K extends keyof HTMLElementTagNameMap,
> extends HTMLElement {
  widget: HTMLElementTagNameMap[K];

  constructor(tagName: K) {
    super();
    this.widget = document.createElement(tagName);
    const attributes: Attr[] = []; // We need to make a copy to delete while iterating
    for (const attr of this.attributes) {
      attributes.push(attr);
    }

    for (const attr of attributes) {
      this.removeAttributeNode(attr);
      this.widget.setAttributeNode(attr);
    }
    this.appendChild(this.widget);
  }
}
