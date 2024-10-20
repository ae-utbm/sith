import "tom-select/dist/css/tom-select.css";
import { inheritHtmlElement, registerComponent } from "#core:utils/web-components";
import TomSelect from "tom-select";
import type {
  RecursivePartial,
  TomLoadCallback,
  TomOption,
  TomSettings,
} from "tom-select/dist/types/types";
import type { escape_html } from "tom-select/dist/types/utils";
import {
  type GroupSchema,
  type UserProfileSchema,
  groupSearchGroup,
  userSearchUsers,
} from "#openapi";

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
    for (const option of Array.from(this.children).filter(
      (child) => child.tagName.toLowerCase() === "option",
    )) {
      this.removeChild(option);
      this.node.appendChild(option);
    }
    this.widget = new TomSelect(this.node, this.tomSelectSettings());
    this.attachBehaviors();
  }

  protected shouldLoad(query: string) {
    console.log(this);
    return query.length >= this.minCharNumberForSearch; // Avoid launching search with less than setup number of characters
  }

  protected tomSelectSettings(): RecursivePartial<TomSettings> {
    return {
      plugins: {
        // biome-ignore lint/style/useNamingConvention: this is required by the api
        remove_button: {
          title: gettext("Remove"),
        },
      },
      persist: false,
      maxItems: this.node.multiple ? this.max : 1,
      closeAfterSelect: true,
      loadThrottle: this.delay,
      placeholder: this.placeholder,
      shouldLoad: (query: string) => this.shouldLoad(query), // wraps the method to avoid shadowing `this` by the one from tom-select
      render: {
        option: (item: TomOption, sanitize: typeof escape_html) => {
          return `<div class="select-item">
            <span class="select-item-text">${sanitize(item.text)}</span>
          </div>`;
        },
        item: (item: TomOption, sanitize: typeof escape_html) => {
          return `<span>${sanitize(item.text)}</span>`;
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
    /* Called once the widget has been initialized */
  }
}

abstract class AjaxSelect extends AutocompleteSelect {
  protected filter?: (items: TomOption[]) => TomOption[] = null;
  protected minCharNumberForSearch = 2;

  protected abstract valueField: string;
  protected abstract labelField: string;
  protected abstract searchField: string[];

  protected abstract renderOption(
    item: TomOption,
    sanitize: typeof escape_html,
  ): string;
  protected abstract renderItem(item: TomOption, sanitize: typeof escape_html): string;
  protected abstract search(query: string): Promise<TomOption[]>;

  public setFilter(filter?: (items: TomOption[]) => TomOption[]) {
    this.filter = filter;
  }

  protected shouldLoad(query: string) {
    const resp = super.shouldLoad(query);
    /* Force order sync with backend if no client side filtering is set */
    if (!resp && this.searchField.length === 0) {
      this.widget.clearOptions();
    }
    return resp;
  }

  protected async loadFunction(query: string, callback: TomLoadCallback) {
    /* Force order sync with backend if no client side filtering is set */
    if (this.searchField.length === 0) {
      this.widget.clearOptions();
    }

    const resp = await this.search(query);

    if (this.filter) {
      callback(this.filter(resp), []);
    } else {
      callback(resp, []);
    }
  }

  protected tomSelectSettings(): RecursivePartial<TomSettings> {
    return {
      ...super.tomSelectSettings(),
      hideSelected: true,
      diacritics: true,
      duplicates: false,
      valueField: this.valueField,
      labelField: this.labelField,
      searchField: this.searchField,
      load: (query: string, callback: TomLoadCallback) =>
        this.loadFunction(query, callback), // wraps the method to avoid shadowing `this` by the one from tom-select
      render: {
        ...super.tomSelectSettings().render,
        option: this.renderOption,
        item: this.renderItem,
      },
    };
  }

  protected attachBehaviors() {
    super.attachBehaviors();

    // Gather selected options, they must be added with slots like `<slot>json</slot>`
    for (const value of Array.from(this.children)
      .filter((child) => child.tagName.toLowerCase() === "slot")
      .map((slot) => JSON.parse(slot.innerHTML))) {
      this.widget.addOption(value, false);
      this.widget.addItem(value[this.valueField]);
    }
  }
}

@registerComponent("user-ajax-select")
export class UserAjaxSelect extends AjaxSelect {
  protected valueField = "id";
  protected labelField = "display_name";
  protected searchField: string[] = []; // Disable local search filter and rely on tested backend

  protected async search(query: string): Promise<TomOption[]> {
    const resp = await userSearchUsers({ query: { search: query } });
    if (resp.data) {
      return resp.data.results;
    }
    return [];
  }

  protected renderOption(item: UserProfileSchema, sanitize: typeof escape_html) {
    return `<div class="select-item">
            <img
              src="${sanitize(item.profile_pict)}"
              alt="${sanitize(item.display_name)}"
              onerror="this.src = '/static/core/img/unknown.jpg'" 
            />
            <span class="select-item-text">${sanitize(item.display_name)}</span>
          </div>`;
  }

  protected renderItem(item: UserProfileSchema, sanitize: typeof escape_html) {
    return `<span>${sanitize(item.display_name)}</span>`;
  }
}

@registerComponent("group-ajax-select")
export class GroupsAjaxSelect extends AjaxSelect {
  protected valueField = "id";
  protected labelField = "name";
  protected searchField = ["name"];

  protected async search(query: string): Promise<TomOption[]> {
    const resp = await groupSearchGroup({ query: { search: query } });
    if (resp.data) {
      return resp.data.results;
    }
    return [];
  }

  protected renderOption(item: GroupSchema, sanitize: typeof escape_html) {
    return `<div class="select-item">
            <span class="select-item-text">${sanitize(item.name)}</span>
          </div>`;
  }

  protected renderItem(item: GroupSchema, sanitize: typeof escape_html) {
    return `<span>${sanitize(item.name)}</span>`;
  }
}
