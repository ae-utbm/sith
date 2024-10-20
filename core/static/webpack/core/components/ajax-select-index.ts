import "tom-select/dist/css/tom-select.default.css";
import { registerComponent } from "#core:utils/web-components";
import type { TomOption } from "tom-select/dist/types/types";
import type { escape_html } from "tom-select/dist/types/utils";
import {
  type GroupSchema,
  type UserProfileSchema,
  groupSearchGroup,
  userSearchUsers,
} from "#openapi";

import {
  AjaxSelect,
  AutoCompleteSelectBase,
} from "#core:core/components/ajax-select-base";

@registerComponent("autocomplete-select")
export class AutoCompleteSelect extends AutoCompleteSelectBase {}

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
