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

abstract class AjaxSelectBase extends inheritHtmlElement("select") {
  static observedAttributes = ["delay", "placeholder", "max"];
  public widget: TomSelect;

  private delay: number | null = null;
  private placeholder = "";
  private max: number | null = null;

  attributeChangedCallback(name: string, _oldValue?: string, newValue?: string) {
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
      default: {
        return;
      }
    }
  }

  constructor() {
    super();

    window.addEventListener("DOMContentLoaded", () => {
      this.configureTomSelect(this.defaultTomSelectSettings());
      this.setDefaultTomSelectBehaviors();
    });
  }

  private defaultTomSelectSettings(): RecursivePartial<TomSettings> {
    return {
      maxItems: this.max,
      loadThrottle: this.delay,
      placeholder: this.placeholder,
    };
  }

  private setDefaultTomSelectBehaviors() {
    // Allow removing selected items by clicking on them
    this.widget.on("item_select", (item: TomItem) => {
      this.widget.removeItem(item);
    });
    // Remove typed text once an item has been selected
    this.widget.on("item_add", () => {
      this.widget.setTextboxValue("");
    });
  }

  abstract configureTomSelect(defaultSettings: RecursivePartial<TomSettings>): void;
}

@registerComponent("user-ajax-select")
export class UserAjaxSelect extends AjaxSelectBase {
  public filter?: <T>(items: T[]) => T[];

  configureTomSelect(defaultSettings: RecursivePartial<TomSettings>) {
    const minCharNumberForSearch = 2;
    this.widget = new TomSelect(this.node, {
      ...defaultSettings,
      hideSelected: true,
      diacritics: true,
      duplicates: false,
      valueField: "id",
      labelField: "display_name",
      searchField: [], // Disable local search filter and rely on tested backend
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
  }
}
