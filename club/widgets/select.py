from django.forms import Select, SelectMultiple

from club.models import Club
from club.schemas import ClubSchema
from core.views.widgets.select import AutoCompleteSelectMixin


class AutoCompleteSelectClub(AutoCompleteSelectMixin, Select):
    component_name = "club-ajax-select"
    model = Club
    schema = ClubSchema

    js = [
        "webpack/club/components/ajax-select-index.ts",
    ]


class AutoCompleteSelectMultipleClub(AutoCompleteSelectMixin, SelectMultiple):
    component_name = "club-ajax-select"
    model = Club
    schema = ClubSchema

    js = [
        "webpack/club/components/ajax-select-index.ts",
    ]
