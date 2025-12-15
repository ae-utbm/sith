from pydantic import TypeAdapter

from core.views.widgets.ajax_select import (
    AutoCompleteSelect,
    AutoCompleteSelectMultiple,
)
from counter.models import Counter, Product, ProductType
from counter.schemas import (
    ProductTypeSchema,
    SimpleProductSchema,
    SimplifiedCounterSchema,
)
from core.models import User
from core.schemas import UserProfileSchema

_js = ["bundled/counter/components/ajax-select-index.ts"]


class AutoCompleteSelectUserCounter(AutoCompleteSelect):
    component_name = "user-counter-ajax-select"
    model = User
    adapter = TypeAdapter(list[UserProfileSchema])
    js = _js


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
    adapter = TypeAdapter(list[SimpleProductSchema])
    js = _js


class AutoCompleteSelectMultipleProduct(AutoCompleteSelectMultiple):
    component_name = "product-ajax-select"
    model = Product
    adapter = TypeAdapter(list[SimpleProductSchema])
    js = _js


class AutoCompleteSelectProductType(AutoCompleteSelect):
    component_name = "product-type-ajax-select"
    model = ProductType
    adapter = TypeAdapter(list[ProductTypeSchema])
    js = _js


class AutoCompleteSelectMultipleProductType(AutoCompleteSelectMultiple):
    component_name = "product-type-ajax-select"
    model = ProductType
    adapter = TypeAdapter(list[ProductTypeSchema])
    js = _js
