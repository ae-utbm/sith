from pydantic import TypeAdapter

from core.views.widgets.select import (
    AutoCompleteSelect,
    AutoCompleteSelectMultiple,
)
from sas.models import Album
from sas.schemas import AlbumSchema

_js = ["bundled/sas/components/ajax-select-index.ts"]


class AutoCompleteSelectAlbum(AutoCompleteSelect):
    component_name = "album-ajax-select"
    model = Album
    adapter = TypeAdapter(list[AlbumSchema])

    js = _js


class AutoCompleteSelectMultipleAlbum(AutoCompleteSelectMultiple):
    component_name = "album-ajax-select"
    model = Album
    adapter = TypeAdapter(list[AlbumSchema])

    js = _js
