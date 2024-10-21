from core.views.widgets.select import AutoCompleteSelect, AutoCompleteSelectMultiple
from counter.models import Counter, Product
from counter.schemas import ProductSchema, SimplifiedCounterSchema

_js = ["webpack/counter/components/ajax-select-index.ts"]


class AutoCompleteSelectCounter(AutoCompleteSelect):
    component_name = "counter-ajax-select"
    model = Counter
    schema = SimplifiedCounterSchema
    js = _js


class AutoCompleteSelectMultipleCounter(AutoCompleteSelectMultiple):
    component_name = "counter-ajax-select"
    model = Counter
    schema = SimplifiedCounterSchema
    js = _js


class AutoCompleteSelectProduct(AutoCompleteSelect):
    component_name = "product-ajax-select"
    model = Product
    schema = ProductSchema
    js = _js


class AutoCompleteSelectMultipleProduct(AutoCompleteSelectMultiple):
    component_name = "product-ajax-select"
    model = Product
    schema = ProductSchema
    js = _js
