from pydantic import TypeAdapter

from core.views.widgets.select import AutoCompleteSelect, AutoCompleteSelectMultiple
from counter.models import Counter, Product
from counter.schemas import ProductSchema, SimplifiedCounterSchema

_js = ["bundled/counter/components/ajax-select-index.ts"]


class AutoCompleteSelectCounter(AutoCompleteSelect):
    component_name = "counter-ajax-select"
    model = Counter
    adapter = TypeAdapter(list[SimplifiedCounterSchema])
    js = _js


class AutoCompleteSelectMultipleCounter(AutoCompleteSelectMultiple):
    component_name = "counter-ajax-select"
    model = Counter
    adapter = TypeAdapter(list[SimplifiedCounterSchema])
    js = _js


class AutoCompleteSelectProduct(AutoCompleteSelect):
    component_name = "product-ajax-select"
    model = Product
    adapter = TypeAdapter(list[ProductSchema])
    js = _js


class AutoCompleteSelectMultipleProduct(AutoCompleteSelectMultiple):
    component_name = "product-ajax-select"
    model = Product
    adapter = TypeAdapter(list[ProductSchema])
    js = _js
