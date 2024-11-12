from pydantic import TypeAdapter

from club.models import Club
from club.schemas import ClubSchema
from core.views.widgets.select import AutoCompleteSelect, AutoCompleteSelectMultiple

_js = ["webpack/club/components/ajax-select-index.ts"]


class AutoCompleteSelectClub(AutoCompleteSelect):
    component_name = "club-ajax-select"
    model = Club
    adapter = TypeAdapter(list[ClubSchema])

    js = _js


class AutoCompleteSelectMultipleClub(AutoCompleteSelectMultiple):
    component_name = "club-ajax-select"
    model = Club
    adapter = TypeAdapter(list[ClubSchema])

    js = _js
