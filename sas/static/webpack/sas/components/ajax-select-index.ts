import { AjaxSelect } from "#core:core/components/ajax-select-base";
import { registerComponent } from "#core:utils/web-components";
import type { TomOption } from "tom-select/dist/types/types";
import type { escape_html } from "tom-select/dist/types/utils";
import { type AlbumSchema, albumSearchAlbum } from "#openapi";

@registerComponent("album-ajax-select")
export class AlbumAjaxSelect extends AjaxSelect {
  protected valueField = "id";
  protected labelField = "path";
  protected searchField = ["path", "name"];

  protected async search(query: string): Promise<TomOption[]> {
    const resp = await albumSearchAlbum({ query: { search: query } });
    if (resp.data) {
      return resp.data.results;
    }
    return [];
  }

  protected renderOption(item: AlbumSchema, sanitize: typeof escape_html) {
    return `<div class="select-item">
            <span class="select-item-text">${sanitize(item.path)}</span>
          </div>`;
  }

  protected renderItem(item: AlbumSchema, sanitize: typeof escape_html) {
    return `<span>${sanitize(item.path)}</span>`;
  }
}
