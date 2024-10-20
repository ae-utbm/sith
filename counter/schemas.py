from datetime import datetime
from typing import Annotated

from annotated_types import MinLen
from ninja import Field, FilterSchema, ModelSchema
from pydantic import Field

from counter.models import Counter, Permanency, Product


class CounterSchema(ModelSchema):
    class Meta:
        model = Counter
        fields = ["id", "name", "type"]


class PermanencySchema(ModelSchema):
    counter: CounterSchema

    class Meta:
        model = Permanency
        fields = ["start", "end"]


class PermanencyFilterSchema(FilterSchema):
    start_after: datetime | None = Field(None, q="start__gte")
    start_before: datetime | None = Field(None, q="start__lte")
    end_after: datetime | None = Field(None, q="end__gte")
    end_before: datetime | None = Field(None, q="end__lte")
    counter: set[int] | None = Field(None, q="counter_id__in")


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
