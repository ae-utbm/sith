import { inheritHtmlElement, registerComponent } from "#core:utils/web-components.ts";

/**
 * Web component used to import css files only once
 * If called multiple times or the file was already imported, it does nothing
 **/
@registerComponent("link-once")
export class LinkOnce extends inheritHtmlElement("link") {
  connectedCallback() {
    super.connectedCallback(false);
    // We get href from node.attributes instead of node.href to avoid getting the domain part
    const href = this.node.attributes.getNamedItem("href").nodeValue;
    if (document.querySelectorAll(`link[href='${href}']`).length === 0) {
      this.appendChild(this.node);
    }
  }
}

/**
 * Web component used to import javascript files only once
 * If called multiple times or the file was already imported, it does nothing
 **/
@registerComponent("script-once")
export class ScriptOnce extends inheritHtmlElement("script") {
  connectedCallback() {
    super.connectedCallback(false);
    // We get src from node.attributes instead of node.src to avoid getting the domain part
    const src = this.node.attributes.getNamedItem("src").nodeValue;
    if (document.querySelectorAll(`script[src='${src}']`).length === 0) {
      this.appendChild(this.node);
    }
  }
}
