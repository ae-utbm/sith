import type { TomOption } from "tom-select/src/types";
import type { escape_html } from "tom-select/src/utils";
import { AjaxSelect } from "#core:core/components/ajax-select-base";
import { registerComponent } from "#core:utils/web-components";
import {
  type CounterSchema,
  counterSearchCounter,
  type ProductTypeSchema,
  productSearchProducts,
  producttypeFetchAll,
  type SimpleProductSchema,
} from "#openapi";

@registerComponent("product-ajax-select")
export class ProductAjaxSelect extends AjaxSelect {
  protected valueField = "id";
  protected labelField = "name";
  protected searchField = ["code", "name"];

  protected async search(query: string): Promise<TomOption[]> {
    const resp = await productSearchProducts({
      // biome-ignore lint/style/useNamingConvention: API is snake_case
      query: { search: query, is_archived: false },
    });
    if (resp.data) {
      return resp.data.results;
    }
    return [];
  }

  private getName(item: SimpleProductSchema, sanitize: typeof escape_html): string {
    return item.code ? `${sanitize(item.code)} - ${sanitize(item.name)}` : item.name;
  }

  protected renderOption(item: SimpleProductSchema, sanitize: typeof escape_html) {
    return `<div class="select-item">
            <span class="select-item-text">${this.getName(item, sanitize)}</span>
          </div>`;
  }

  protected renderItem(item: SimpleProductSchema, sanitize: typeof escape_html) {
    return `<span>${this.getName(item, sanitize)}</span>`;
  }
}

@registerComponent("product-type-ajax-select")
export class ProductTypeAjaxSelect extends AjaxSelect {
  protected valueField = "id";
  protected labelField = "name";
  protected searchField = ["name"];
  private productTypes = null as ProductTypeSchema[] | null;

  protected async search(query: string): Promise<TomOption[]> {
    // The production database has a grand total of 26 product types
    // and the filter logic is really simple.
    // Thus, it's appropriate to fetch all product types during first use,
    // then to reuse the result again and again.
    if (this.productTypes === null) {
      this.productTypes = (await producttypeFetchAll()).data || [];
    }
    return this.productTypes.filter((t) =>
      t.name.toLowerCase().includes(query.toLowerCase()),
    );
  }

  protected renderOption(item: ProductTypeSchema, sanitize: typeof escape_html) {
    return `<div class="select-item">
            <span class="select-item-text">${sanitize(item.name)}</span>
          </div>`;
  }

  protected renderItem(item: ProductTypeSchema, sanitize: typeof escape_html) {
    return `<span>${sanitize(item.name)}</span>`;
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
