import "tom-select/dist/css/tom-select.css";
import { inheritHtmlElement, registerComponent } from "#core:utils/web-components";
import TomSelect from "tom-select";
import type { TomItem, TomLoadCallback, TomOption } from "tom-select/dist/types/types";
import type { escape_html } from "tom-select/dist/types/utils";
import { type UserProfileSchema, userSearchUsers } from "#openapi";

@registerComponent("ajax-select")
export class AjaxSelect extends inheritHtmlElement("select") {
  public widget: TomSelect;
  public filter?: <T>(items: T[]) => T[];

  constructor() {
    super();

    window.addEventListener("DOMContentLoaded", () => {
      this.loadTomSelect();
    });
  }

  loadTomSelect() {
    const minCharNumberForSearch = 2;
    let maxItems = 1;

    if (this.node.multiple) {
      maxItems = Number.parseInt(this.node.dataset.max) ?? null;
    }

    this.widget = new TomSelect(this.node, {
      hideSelected: true,
      diacritics: true,
      duplicates: false,
      maxItems: maxItems,
      loadThrottle: Number.parseInt(this.node.dataset.delay) ?? null,
      valueField: "id",
      labelField: "display_name",
      searchField: ["display_name", "nick_name", "first_name", "last_name"],
      placeholder: this.node.dataset.placeholder ?? "",
      shouldLoad: (query: string) => {
        return query.length >= minCharNumberForSearch; // Avoid launching search with less than 2 characters
      },
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
        // biome-ignore lint/style/useNamingConvention: that's how it's defined
        not_loading: (data: TomOption, _sanitize: typeof escape_html) => {
          return `<div class="no-results">${interpolate(gettext("You need to type %(number)s more characters"), { number: minCharNumberForSearch - data.input.length }, true)}</div>`;
        },
        // biome-ignore lint/style/useNamingConvention: that's how it's defined
        no_results: (_data: TomOption, _sanitize: typeof escape_html) => {
          return `<div class="no-results">${gettext("No results found")}</div>`;
        },
      },
    });

    // Allow removing selected items by clicking on them
    this.widget.on("item_select", (item: TomItem) => {
      this.widget.removeItem(item);
    });
    // Remove typed text once an item has been selected
    this.widget.on("item_add", () => {
      this.widget.setTextboxValue("");
    });
  }
}
