import { AjaxSelect } from "#core:core/components/ajax-select-base";
import { registerComponent } from "#core:utils/web-components";
import type { TomOption } from "tom-select/dist/types/types";
import type { escape_html } from "tom-select/dist/types/utils";
import {
  type CounterSchema,
  type ProductSchema,
  counterSearchCounter,
  productSearchProducts,
} from "#openapi";

@registerComponent("product-ajax-select")
export class ProductAjaxSelect extends AjaxSelect {
  protected valueField = "id";
  protected labelField = "name";
  protected searchField = ["code", "name"];

  protected async search(query: string): Promise<TomOption[]> {
    const resp = await productSearchProducts({ query: { search: query } });
    if (resp.data) {
      return resp.data.results;
    }
    return [];
  }

  protected renderOption(item: ProductSchema, sanitize: typeof escape_html) {
    return `<div class="select-item">
            <span class="select-item-text">${sanitize(item.code)} - ${sanitize(item.name)}</span>
          </div>`;
  }

  protected renderItem(item: ProductSchema, sanitize: typeof escape_html) {
    return `<span>${sanitize(item.code)} - ${sanitize(item.name)}</span>`;
  }
}

@registerComponent("counter-ajax-select")
export class CounterAjaxSelect extends AjaxSelect {
  protected valueField = "id";
  protected labelField = "name";
  protected searchField = ["code", "name"];

  protected async search(query: string): Promise<TomOption[]> {
    const resp = await counterSearchCounter({ query: { search: query } });
    if (resp.data) {
      return resp.data.results;
    }
    return [];
  }

  protected renderOption(item: CounterSchema, sanitize: typeof escape_html) {
    return `<div class="select-item">
            <span class="select-item-text">${sanitize(item.name)}</span>
          </div>`;
  }

  protected renderItem(item: CounterSchema, sanitize: typeof escape_html) {
    return `<span>${sanitize(item.name)}</span>`;
  }
}
