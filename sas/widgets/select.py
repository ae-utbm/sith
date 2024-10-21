from django.forms import Select, SelectMultiple

from core.views.widgets.select import AutoCompleteSelectMixin
from sas.models import Album
from sas.schemas import AlbumSchema


class AutoCompleteSelectAlbum(AutoCompleteSelectMixin, Select):
    component_name = "album-ajax-select"
    model = Album
    schema = AlbumSchema

    js = [
        "webpack/sas/components/ajax-select-index.ts",
    ]


class AutoCompleteSelectMultipleAlbum(AutoCompleteSelectMixin, SelectMultiple):
    component_name = "album-ajax-select"
    model = Album
    schema = AlbumSchema

    js = [
        "webpack/sas/components/ajax-select-index.ts",
    ]
