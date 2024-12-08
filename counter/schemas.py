from typing import Annotated

from annotated_types import MinLen
from ninja import Field, FilterSchema, ModelSchema

from core.schemas import SimpleUserSchema
from counter.models import Counter, Customer, Product


class CounterSchema(ModelSchema):
    barmen_list: list[SimpleUserSchema]
    is_open: bool

    class Meta:
        model = Counter
        fields = ["id", "name", "type", "club", "products"]


class CustomerBalance(ModelSchema):
    class Meta:
        model = Customer
        fields = ["amount"]


class CounterFilterSchema(FilterSchema):
    search: Annotated[str, MinLen(1)] = Field(None, q="name__icontains")


class SimplifiedCounterSchema(ModelSchema):
    class Meta:
        model = Counter
        fields = ["id", "name"]


class ProductSchema(ModelSchema):
    class Meta:
        model = Product
        fields = ["id", "name", "code"]
