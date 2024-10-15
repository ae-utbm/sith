import "tom-select/dist/css/tom-select.css";
import TomSelect from "tom-select";
import type { TomItem, TomLoadCallback } from "tom-select/dist/types/types";
import type { escape_html } from "tom-select/dist/types/utils";
import { type UserProfileSchema, userSearchUsers } from "#openapi";

export class AjaxSelect extends HTMLSelectElement {
  widget: TomSelect;
  filter?: <T>(items: T[]) => T[];

  constructor() {
    super();

    window.addEventListener("DOMContentLoaded", () => {
      this.loadTomSelect();
    });
  }

  loadTomSelect() {
    let maxItems = 1;

    if (this.multiple) {
      maxItems = Number.parseInt(this.dataset.max) ?? null;
    }

    this.widget = new TomSelect(this, {
      hideSelected: true,
      maxItems: maxItems,
      loadThrottle: Number.parseInt(this.dataset.delay) ?? null,
      valueField: "id",
      labelField: "display_name",
      searchField: ["display_name", "nick_name", "first_name", "last_name"],
      placeholder: this.dataset.placeholder ?? "",
      load: (query: string, callback: TomLoadCallback) => {
        userSearchUsers({
          query: {
            search: query,
          },
        }).then((response) => {
          if (response.data) {
            if (this.filter) {
              callback(this.filter(response.data.results), []);
            } else {
              callback(response.data.results, []);
            }
            return;
          }
          callback([], []);
        });
      },
      render: {
        option: (item: UserProfileSchema, sanitize: typeof escape_html) => {
          return `<div class="select-item">
            <img
              src="${sanitize(item.profile_pict)}"
              alt="${sanitize(item.display_name)}"
              onerror="this.src = '/static/core/img/unknown.jpg'" 
            />
            <span class="select-item-text">${sanitize(item.display_name)}</span>
          </div>`;
        },
        item: (item: UserProfileSchema, sanitize: typeof escape_html) => {
          return `<span><i class="fa fa-times"></i>${sanitize(item.display_name)}</span>`;
        },
      },
    });

    this.widget.on("item_select", (item: TomItem) => {
      this.widget.removeItem(item);
    });
  }
}

window.customElements.define("ajax-select", AjaxSelect, { extends: "select" });
