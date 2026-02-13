import type { TomOption } from "tom-select/dist/types/types";
import type { escape_html } from "tom-select/dist/types/utils";
import { AjaxSelect } from "#core:core/components/ajax-select-base.ts";
import { registerComponent } from "#core:utils/web-components.ts";
import { type ClubSchema, clubSearchClub } from "#openapi";

@registerComponent("club-ajax-select")
export class ClubAjaxSelect extends AjaxSelect {
  protected valueField = "id";
  protected labelField = "name";
  protected searchField = ["code", "name"];

  protected async search(query: string): Promise<TomOption[]> {
    const resp = await clubSearchClub({ query: { search: query } });
    if (resp.data) {
      return resp.data.results;
    }
    return [];
  }

  protected renderOption(item: ClubSchema, sanitize: typeof escape_html) {
    return `<div class="select-item">
            <span class="select-item-text">${sanitize(item.name)}</span>
          </div>`;
  }

  protected renderItem(item: ClubSchema, sanitize: typeof escape_html) {
    return `<span>${sanitize(item.name)}</span>`;
  }
}
