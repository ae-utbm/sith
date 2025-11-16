from datetime import datetime
from typing import Annotated, Self

from django.urls import reverse
from ninja import FilterLookup, FilterSchema, ModelSchema, Schema
from pydantic import model_validator

from club.schemas import SimpleClubSchema
from core.schemas import GroupSchema, NonEmptyStr, SimpleUserSchema
from counter.models import Counter, Product, ProductType


class CounterSchema(ModelSchema):
    barmen_list: list[SimpleUserSchema]
    is_open: bool

    class Meta:
        model = Counter
        fields = ["id", "name", "type", "club", "products"]


class CounterFilterSchema(FilterSchema):
    search: Annotated[NonEmptyStr | None, FilterLookup("name__icontains")] = None


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
    club: SimpleClubSchema
    product_type: SimpleProductTypeSchema | None
    url: str

    @staticmethod
    def resolve_url(obj: Product) -> str:
        return reverse("counter:product_edit", kwargs={"product_id": obj.id})


class ProductFilterSchema(FilterSchema):
    search: Annotated[
        NonEmptyStr | None, FilterLookup(["name__icontains", "code__icontains"])
    ] = None
    is_archived: Annotated[bool | None, FilterLookup("archived")] = None
    buying_groups: Annotated[set[int] | None, FilterLookup("buying_groups__in")] = None
    product_type: Annotated[set[int] | None, FilterLookup("product_type__in")] = None
    club: Annotated[set[int] | None, FilterLookup("club__in")] = None
    counter: Annotated[set[int] | None, FilterLookup("counters__in")] = None


class SaleFilterSchema(FilterSchema):
    before: Annotated[datetime | None, FilterLookup("date__lt")] = None
    after: Annotated[datetime | None, FilterLookup("date__gt")] = None
    counters: Annotated[set[int] | None, FilterLookup("counter__in")] = None
    products: Annotated[set[int] | None, FilterLookup("product__in")] = None
