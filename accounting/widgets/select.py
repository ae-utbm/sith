from django.forms import Select, SelectMultiple

from accounting.models import ClubAccount, Company
from accounting.schemas import ClubAccountSchema, CompanySchema
from core.views.widgets.select import AutoCompleteSelectMixin


class AutoCompleteSelectClubAccount(AutoCompleteSelectMixin, Select):
    component_name = "club-account-ajax-select"
    model = ClubAccount
    schema = ClubAccountSchema

    js = [
        "webpack/accounting/components/ajax-select-index.ts",
    ]


class AutoCompleteSelectMultipleClubAccount(AutoCompleteSelectMixin, SelectMultiple):
    component_name = "club-account-ajax-select"
    model = ClubAccount
    schema = ClubAccountSchema

    js = [
        "webpack/accounting/components/ajax-select-index.ts",
    ]


class AutoCompleteSelectCompany(AutoCompleteSelectMixin, Select):
    component_name = "company-ajax-select"
    model = Company
    schema = CompanySchema

    js = [
        "webpack/accounting/components/ajax-select-index.ts",
    ]


class AutoCompleteSelectMultipleCompany(AutoCompleteSelectMixin, SelectMultiple):
    component_name = "company-ajax-select"
    model = Company
    schema = CompanySchema

    js = [
        "webpack/accounting/components/ajax-select-index.ts",
    ]
