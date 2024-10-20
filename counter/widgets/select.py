from django.forms import Select, SelectMultiple

from core.views.widgets.select import AutoCompleteSelectMixin
from counter.models import Counter, Product
from counter.schemas import ProductSchema, SimplifiedCounterSchema


class CounterAutoCompleteSelectMixin(AutoCompleteSelectMixin):
    js = [
        "webpack/counter/components/ajax-select-index.ts",
    ]


class AutoCompleteSelectCounter(CounterAutoCompleteSelectMixin, Select):
    component_name = "counter-ajax-select"
    model = Counter
    schema = SimplifiedCounterSchema


class AutoCompleteSelectMultipleCounter(CounterAutoCompleteSelectMixin, SelectMultiple):
    component_name = "counter-ajax-select"
    model = Counter
    schema = SimplifiedCounterSchema


class AutoCompleteSelectProduct(CounterAutoCompleteSelectMixin, Select):
    component_name = "product-ajax-select"
    model = Product
    schema = ProductSchema


class AutoCompleteSelectMultipleProduct(CounterAutoCompleteSelectMixin, SelectMultiple):
    component_name = "product-ajax-select"
    model = Product
    schema = ProductSchema
