import { registerComponent } from "#core:utils/web-components";
import { html, render } from "lit-html";
import { unsafeHTML } from "lit-html/directives/unsafe-html.js";

@registerComponent("ui-tab")
export class Tab extends HTMLElement {
  static observedAttributes = ["title", "active"];
  private description = "";
  private inner = "";
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
    this.dispatchEvent(new CustomEvent("ui-tab-updated", { bubbles: true }));
  }

  getButtonTemplate() {
    return html`
    	<button
	    	role="tab"
	    	?aria-selected=${this.active}
    		class="tab-header clickable ${this.active ? "active" : ""}"
    		@click="${() => this.setActive(true)}"
    	>
    		${this.description}
    	</button>
    `;
  }
  getContentTemplate() {
    return html`
    	<section
    		class="tab-section"
    		?hidden=${!this.active}
    	>
	    	${unsafeHTML(this.getContentHtml())}
	    </section>
    `;
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
  }

  getContentHtml() {
    const content = this.getElementsByClassName("tab-section")[0];
    if (content !== undefined) {
      return content.innerHTML;
    }
    return this.inner;
  }

  setContentHtml(value: string) {
    const content = this.getElementsByClassName("tab-section")[0];
    if (content !== undefined) {
      content.innerHTML = value;
    }
    this.inner = value;
  }
}

@registerComponent("ui-tab-group")
export class TabGroup extends HTMLElement {
  private node: HTMLDivElement;

  connectedCallback() {
    this.node = document.createElement("div");
    this.node.classList.add("tabs", "shadow");
    this.appendChild(this.node);

    this.addEventListener("ui-tab-activated", (event: CustomEvent) => {
      const target = event.detail as Tab;
      for (const tab of this.getElementsByTagName("ui-tab") as HTMLCollectionOf<Tab>) {
        if (tab !== target) {
          tab.setActive(false);
        }
      }
    });
    this.addEventListener("ui-tab-updated", () => {
      this.render();
    });

    this.render();
  }

  render() {
    const tabs = Array.prototype.slice.call(
      this.getElementsByTagName("ui-tab"),
    ) as Tab[];
    render(
      html`
      	<div class="tab-headers">
      		${tabs.map((tab) => tab.getButtonTemplate())}
      	</div>
      	<div class="tab-content">
      		${tabs.map((tab) => tab.getContentTemplate())}
      	</div>
    `,
      this.node,
    );
  }
}
