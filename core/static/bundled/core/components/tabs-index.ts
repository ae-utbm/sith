import { registerComponent } from "#core:utils/web-components";
import { html, render } from "lit-html";
import { unsafeHTML } from "lit-html/directives/unsafe-html.js";

@registerComponent("ui-tab")
export class Tab extends HTMLElement {
  static observedAttributes = ["title", "active"];
  private description = "";
  private inner = "";
  private initialized = false;
  private active = false;

  attributeChangedCallback(name: string, _oldValue?: string, newValue?: string) {
    const activeOld = this.active;
    this.active = this.hasAttribute("active");
    if (this.active !== activeOld && this.active) {
      this.dispatchEvent(
        new CustomEvent("ui-tab-activated", { detail: this, bubbles: true }),
      );
    }

    if (name === "title") {
      this.description = newValue;
    }

    this.render();
  }

  render() {
    if (!this.initialized) {
      return;
    }
    const active = this.active ? "active" : "";
    const tabContent = this.getContentHtml();
    const content = html`
    	<button
	    	role="tab"
	    	?aria-selected=${active}
    		class="tab-header clickable ${active}"
    		@click="${() => this.setActive(true)}"
    	>
    		${this.description}
    	</button>
    	<section
    		class="tab-content"
    		?hidden=${!active}
    	>
	    	${unsafeHTML(tabContent)}
	    </section>
    `;
    render(content, this);
  }

  setActive(value: boolean) {
    if (value) {
      this.setAttribute("active", "");
    } else {
      this.removeAttribute("active");
    }
  }

  connectedCallback() {
    this.inner = this.innerHTML;
    this.innerHTML = "";
    this.initialized = true;
    this.render();
  }

  getContentHtml() {
    const content = this.getElementsByClassName("tab-content")[0];
    if (content !== undefined) {
      return content.innerHTML;
    }
    return this.inner;
  }

  setContentHtml(value: string) {
    const content = this.getElementsByClassName("tab-content")[0];
    if (content !== undefined) {
      content.innerHTML = value;
    }
    this.inner = value;
    this.render();
  }
}

@registerComponent("ui-tab-group")
export class TabGroup extends HTMLElement {
  connectedCallback() {
    this.classList.add("tabs", "shadow");
    this.addEventListener("ui-tab-activated", (event: CustomEvent) => {
      const target = event.detail as Tab;
      for (const tab of this.getElementsByTagName("ui-tab") as HTMLCollectionOf<Tab>) {
        if (tab !== target) {
          tab.setActive(false);
        }
      }
    });
  }
}
