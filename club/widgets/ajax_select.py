from pydantic import TypeAdapter

from club.models import Club
from club.schemas import SimpleClubSchema
from core.views.widgets.ajax_select import (
    AutoCompleteSelect,
    AutoCompleteSelectMultiple,
)

_js = ["bundled/club/components/ajax-select-index.ts"]


class AutoCompleteSelectClub(AutoCompleteSelect):
    component_name = "club-ajax-select"
    model = Club
    adapter = TypeAdapter(list[SimpleClubSchema])

    js = _js


class AutoCompleteSelectMultipleClub(AutoCompleteSelectMultiple):
    component_name = "club-ajax-select"
    model = Club
    adapter = TypeAdapter(list[SimpleClubSchema])

    js = _js
