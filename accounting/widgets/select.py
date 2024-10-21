from accounting.models import ClubAccount, Company
from accounting.schemas import ClubAccountSchema, CompanySchema
from core.views.widgets.select import AutoCompleteSelect, AutoCompleteSelectMultiple

_js = ["webpack/accounting/components/ajax-select-index.ts"]


class AutoCompleteSelectClubAccount(AutoCompleteSelect):
    component_name = "club-account-ajax-select"
    model = ClubAccount
    schema = ClubAccountSchema

    js = _js


class AutoCompleteSelectMultipleClubAccount(AutoCompleteSelectMultiple):
    component_name = "club-account-ajax-select"
    model = ClubAccount
    schema = ClubAccountSchema

    js = _js


class AutoCompleteSelectCompany(AutoCompleteSelect):
    component_name = "company-ajax-select"
    model = Company
    schema = CompanySchema

    js = _js


class AutoCompleteSelectMultipleCompany(AutoCompleteSelectMultiple):
    component_name = "company-ajax-select"
    model = Company
    schema = CompanySchema

    js = _js
