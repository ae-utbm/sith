import { AjaxSelect } from "#core:core/components/ajax-select-base";
import { registerComponent } from "#core:utils/web-components";
import type { TomOption } from "tom-select/dist/types/types";
import type { escape_html } from "tom-select/dist/types/utils";
import {
  type ClubAccountSchema,
  type CompanySchema,
  accountingSearchClubAccount,
  accountingSearchCompany,
} from "#openapi";

@registerComponent("club-account-ajax-select")
export class ClubAccountAjaxSelect extends AjaxSelect {
  protected valueField = "id";
  protected labelField = "name";
  protected searchField = ["code", "name"];

  protected async search(query: string): Promise<TomOption[]> {
    const resp = await accountingSearchClubAccount({ query: { search: query } });
    if (resp.data) {
      return resp.data.results;
    }
    return [];
  }

  protected renderOption(item: ClubAccountSchema, sanitize: typeof escape_html) {
    return `<div class="select-item">
            <span class="select-item-text">${sanitize(item.name)}</span>
          </div>`;
  }

  protected renderItem(item: ClubAccountSchema, sanitize: typeof escape_html) {
    return `<span>${sanitize(item.name)}</span>`;
  }
}

@registerComponent("company-ajax-select")
export class CompanyAjaxSelect extends AjaxSelect {
  protected valueField = "id";
  protected labelField = "name";
  protected searchField = ["code", "name"];

  protected async search(query: string): Promise<TomOption[]> {
    const resp = await accountingSearchCompany({ query: { search: query } });
    if (resp.data) {
      return resp.data.results;
    }
    return [];
  }

  protected renderOption(item: CompanySchema, sanitize: typeof escape_html) {
    return `<div class="select-item">
            <span class="select-item-text">${sanitize(item.name)}</span>
          </div>`;
  }

  protected renderItem(item: CompanySchema, sanitize: typeof escape_html) {
    return `<span>${sanitize(item.name)}</span>`;
  }
}
