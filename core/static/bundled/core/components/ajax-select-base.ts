import { inheritHtmlElement } from "#core:utils/web-components";
import TomSelect from "tom-select";
import type {
  RecursivePartial,
  TomLoadCallback,
  TomOption,
  TomSettings,
} from "tom-select/dist/types/types";
import type { escape_html } from "tom-select/dist/types/utils";

export class AutoCompleteSelectBase extends inheritHtmlElement("select") {
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
    this.widget = new TomSelect(this.node, this.tomSelectSettings());
    this.attachBehaviors();
  }

  protected shouldLoad(query: string) {
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

export abstract class AjaxSelect extends AutoCompleteSelectBase {
  protected filter?: (items: TomOption[]) => TomOption[] = null;
  protected minCharNumberForSearch = 2;
  /**
   * A cache of researches that have been made using this input.
   * For each record, the key is the user's query and the value
   * is the list of results sent back by the server.
   */
  protected cache = {} as Record<string, TomOption[]>;

  protected abstract valueField: string;
  protected abstract labelField: string;
  protected abstract searchField: string[];

  protected abstract renderOption(
    item: TomOption,
    sanitize: typeof escape_html,
  ): string;
  protected abstract renderItem(item: TomOption, sanitize: typeof escape_html): string;
  protected abstract search(query: string): Promise<TomOption[]>;

  private initialValues: TomOption[] = [];
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

    // Check in the cache if this query has already been typed
    // and do an actual HTTP request only if the result isn't cached
    let resp = this.cache[query];
    if (!resp) {
      resp = await this.search(query);
      this.cache[query] = resp;
    }

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

  connectedCallback() {
    /* Capture initial values before they get moved to the inner node and overridden by tom-select */
    const initial = this.querySelector("slot[name='initial']")?.textContent;
    this.initialValues = initial ? JSON.parse(initial) : [];

    super.connectedCallback();
  }

  protected attachBehaviors() {
    super.attachBehaviors();

    // Gather selected options, they must be added with slots like `<slot>json</slot>`
    for (const value of this.initialValues) {
      this.widget.addOption(value, false);
      this.widget.addItem(value[this.valueField]);
    }
  }
}
