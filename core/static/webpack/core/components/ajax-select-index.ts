import "tom-select/dist/css/tom-select.css";
import { inheritHtmlElement, registerComponent } from "#core:utils/web-components";
import TomSelect from "tom-select";
import type {
  RecursivePartial,
  TomItem,
  TomLoadCallback,
  TomOption,
  TomSettings,
} from "tom-select/dist/types/types";
import type { escape_html } from "tom-select/dist/types/utils";
import { type UserProfileSchema, userSearchUsers } from "#openapi";

@registerComponent("autocomplete-select")
class AutocompleteSelect extends inheritHtmlElement("select") {
  static observedAttributes = [
    "delay",
    "placeholder",
    "max",
    "min-characters-for-search",
  ];
  public widget: TomSelect;

  protected minCharNumberForSearch = 0;
  protected delay: number | null = null;
  protected placeholder = "";
  protected max: number | null = null;

  protected attributeChangedCallback(
    name: string,
    _oldValue?: string,
    newValue?: string,
  ) {
    switch (name) {
      case "delay": {
        this.delay = Number.parseInt(newValue) ?? null;
        break;
      }
      case "placeholder": {
        this.placeholder = newValue ?? "";
        break;
      }
      case "max": {
        this.max = Number.parseInt(newValue) ?? null;
        break;
      }
      case "min-characters-for-search": {
        this.minCharNumberForSearch = Number.parseInt(newValue) ?? 0;
        break;
      }
      default: {
        return;
      }
    }
  }

  connectedCallback() {
    super.connectedCallback();
    // Collect all options nodes and put them into the select node
    const options: Element[] = []; // We need to make a copy to delete while iterating
    for (const child of this.children) {
      if (child.tagName.toLowerCase() === "option") {
        options.push(child);
      }
    }
    for (const option of options) {
      this.removeChild(option);
      this.node.appendChild(option);
    }
    this.widget = new TomSelect(this.node, this.tomSelectSettings());
    this.attachBehaviors();
  }

  protected tomSelectSettings(): RecursivePartial<TomSettings> {
    return {
      maxItems: this.node.multiple ? this.max : 1,
      loadThrottle: this.delay,
      placeholder: this.placeholder,
      shouldLoad: (query: string) => {
        return query.length >= this.minCharNumberForSearch; // Avoid launching search with less than 2 characters
      },
      render: {
        option: (item: TomOption, sanitize: typeof escape_html) => {
          return `<div class="select-item">
            <span class="select-item-text">${sanitize(item.text)}</span>
          </div>`;
        },
        item: (item: TomOption, sanitize: typeof escape_html) => {
          return `<span><i class="fa fa-times"></i>${sanitize(item.text)}</span>`;
        },
        // biome-ignore lint/style/useNamingConvention: that's how it's defined
        not_loading: (data: TomOption, _sanitize: typeof escape_html) => {
          return `<div class="no-results">${interpolate(gettext("You need to type %(number)s more characters"), { number: this.minCharNumberForSearch - data.input.length }, true)}</div>`;
        },
        // biome-ignore lint/style/useNamingConvention: that's how it's defined
        no_results: (_data: TomOption, _sanitize: typeof escape_html) => {
          return `<div class="no-results">${gettext("No results found")}</div>`;
        },
      },
    };
  }

  protected attachBehaviors() {
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

@registerComponent("user-ajax-select")
export class UserAjaxSelect extends AutocompleteSelect {
  public filter?: <T>(items: T[]) => T[];

  protected minCharNumberForSearch = 2;

  protected tomSelectSettings(): RecursivePartial<TomSettings> {
    return {
      ...super.tomSelectSettings(),
      hideSelected: true,
      diacritics: true,
      duplicates: false,
      valueField: "id",
      labelField: "display_name",
      searchField: [], // Disable local search filter and rely on tested backend
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
        ...super.tomSelectSettings().render,
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
    };
  }
}
