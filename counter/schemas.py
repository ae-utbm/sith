from typing import Annotated, Self

from annotated_types import MinLen
from django.urls import reverse
from ninja import Field, FilterSchema, ModelSchema, Schema
from pydantic import model_validator

from club.schemas import ClubSchema
from core.schemas import GroupSchema, SimpleUserSchema
from counter.models import Counter, Product, ProductType


class CounterSchema(ModelSchema):
    barmen_list: list[SimpleUserSchema]
    is_open: bool

    class Meta:
        model = Counter
        fields = ["id", "name", "type", "club", "products"]


class CounterFilterSchema(FilterSchema):
    search: Annotated[str, MinLen(1)] = Field(None, q="name__icontains")


class SimplifiedCounterSchema(ModelSchema):
    class Meta:
        model = Counter
        fields = ["id", "name"]


class ProductTypeSchema(ModelSchema):
    class Meta:
        model = ProductType
        fields = ["id", "name", "description", "comment", "icon", "order"]

    url: str

    @staticmethod
    def resolve_url(obj: ProductType) -> str:
        return reverse("counter:product_type_edit", kwargs={"type_id": obj.id})


class SimpleProductTypeSchema(ModelSchema):
    class Meta:
        model = ProductType
        fields = ["id", "name"]


class ReorderProductTypeSchema(Schema):
    below: int | None = None
    above: int | None = None

    @model_validator(mode="after")
    def validate_exclusive(self) -> Self:
        if self.below is None and self.above is None:
            raise ValueError("Either 'below' or 'above' must be set.")
        if self.below is not None and self.above is not None:
            raise ValueError("Only one of 'below' or 'above' must be set.")
        return self


class SimpleProductSchema(ModelSchema):
    class Meta:
        model = Product
        fields = ["id", "name", "code"]


class ProductSchema(ModelSchema):
    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "code",
            "description",
            "purchase_price",
            "selling_price",
            "icon",
            "limit_age",
            "archived",
        ]

    buying_groups: list[GroupSchema]
    club: ClubSchema
    product_type: SimpleProductTypeSchema | None
    url: str

    @staticmethod
    def resolve_url(obj: Product) -> str:
        return reverse("counter:product_edit", kwargs={"product_id": obj.id})


class ProductFilterSchema(FilterSchema):
    search: Annotated[str, MinLen(1)] | None = Field(
        None, q=["name__icontains", "code__icontains"]
    )
    is_archived: bool | None = Field(None, q="archived")
    buying_groups: set[int] | None = Field(None, q="buying_groups__in")
    product_type: set[int] | None = Field(None, q="product_type__in")
    club: set[int] | None = Field(None, q="club__in")
    counter: set[int] | None = Field(None, q="counters__in")
