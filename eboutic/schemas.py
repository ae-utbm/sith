from ninja import ModelSchema, Schema
from pydantic import Field, NonNegativeInt, PositiveInt, TypeAdapter

from counter.models import BillingInfo


class PurchaseItemSchema(Schema):
    product_id: NonNegativeInt = Field(alias="id")
    name: str
    unit_price: float
    quantity: PositiveInt


# The eboutic deals with data that is dict mixed with JSON.
# Hence it would be a hassle to manage it with a proper Schema class,
# and we use a TypeAdapter instead
PurchaseItemList = TypeAdapter(list[PurchaseItemSchema])


class BillingInfoSchema(ModelSchema):
    class Meta:
        model = BillingInfo
        fields = [
            "customer",
            "first_name",
            "last_name",
            "address_1",
            "address_2",
            "zip_code",
            "city",
            "country",
        ]
        fields_optional = ["customer"]
