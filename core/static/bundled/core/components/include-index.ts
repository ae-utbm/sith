import { inheritHtmlElement, registerComponent } from "#core:utils/web-components.ts";

/**
 * Web component used to import css files only once
 * If called multiple times or the file was already imported, it does nothing
 **/
@registerComponent("link-once")
export class LinkOnce extends inheritHtmlElement("link") {
  refresh() {
    this.clearNode();

    // We get href from node.attributes instead of node.href to avoid getting the domain part
    const href = this.node.attributes.getNamedItem("href").nodeValue;
    if (document.querySelectorAll(`link[href='${href}']`).length === 0) {
      this.appendChild(this.node);
    }
  }

  clearNode() {
    while (this.firstChild) {
      this.removeChild(this.lastChild);
    }
  }

  connectedCallback() {
    super.connectedCallback(false);
    this.refresh();
  }

  disconnectedCallback() {
    this.clearNode();

    // This re-triggers link-once elements that still exists and suppressed
    // themeselves once it gets removed from the page
    for (const link of document.getElementsByTagName("link-once")) {
      (link as LinkOnce).refresh();
    }
  }
}

/**
 * Web component used to import javascript files only once
 * If called multiple times or the file was already imported, it does nothing
 **/
@registerComponent("script-once")
export class ScriptOnce extends inheritHtmlElement("script") {
  refresh() {
    this.clearNode();

    // We get src from node.attributes instead of node.src to avoid getting the domain part
    const src = this.node.attributes.getNamedItem("src").nodeValue;
    if (document.querySelectorAll(`script[src='${src}']`).length === 0) {
      this.appendChild(this.node);
    }
  }

  clearNode() {
    while (this.firstChild) {
      this.removeChild(this.lastChild);
    }
  }

  connectedCallback() {
    super.connectedCallback(false);
    this.refresh();
  }

  disconnectedCallback() {
    this.clearNode();

    // This re-triggers script-once elements that still exists and suppressed
    // themeselves once it gets removed from the page
    for (const link of document.getElementsByTagName("script-once")) {
      (link as LinkOnce).refresh();
    }
  }
}
