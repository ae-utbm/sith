from typing import Annotated

from annotated_types import MinLen
from django.urls import reverse
from ninja import Field, FilterSchema, ModelSchema

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
        fields = ["id", "name"]


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
    product_type: ProductTypeSchema | None
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
