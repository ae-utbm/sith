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

abstract class AjaxSelect extends AutocompleteSelect {
  protected filter?: (items: TomOption[]) => TomOption[] = null;
  protected minCharNumberForSearch = 2;

  protected abstract valueField: string;
  protected abstract labelField: string;
  protected abstract renderOption(
    item: TomOption,
    sanitize: typeof escape_html,
  ): string;
  protected abstract renderItem(item: TomOption, sanitize: typeof escape_html): string;
  protected abstract search(query: string): Promise<TomOption[]>;

  public setFilter(filter?: (items: TomOption[]) => TomOption[]) {
    this.filter = filter;
  }

  protected getLoadFunction() {
    // this will be replaced by TomSelect if we don't wrap it that way
    return async (query: string, callback: TomLoadCallback) => {
      const resp = await this.search(query);
      if (this.filter) {
        callback(this.filter(resp), []);
      } else {
        callback(resp, []);
      }
    };
  }

  protected tomSelectSettings(): RecursivePartial<TomSettings> {
    return {
      ...super.tomSelectSettings(),
      hideSelected: true,
      diacritics: true,
      duplicates: false,
      valueField: this.valueField,
      labelField: this.labelField,
      searchField: [], // Disable local search filter and rely on tested backend
      load: this.getLoadFunction(),
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
      this.widget.addOption(value, true);
      this.widget.addItem(value[this.valueField]);
    }
  }
}

@registerComponent("user-ajax-select")
export class UserAjaxSelect extends AjaxSelect {
  protected valueField = "id";
  protected labelField = "display_name";

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
    return `<span><i class="fa fa-times"></i>${sanitize(item.display_name)}</span>`;
  }
}

@registerComponent("group-ajax-select")
export class GroupsAjaxSelect extends AjaxSelect {
  protected valueField = "id";
  protected labelField = "name";

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
    return `<span><i class="fa fa-times"></i>${sanitize(item.name)}</span>`;
  }
}
