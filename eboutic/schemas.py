from typing import Annotated

from ninja import ModelSchema, Schema
from pydantic import Field, NonNegativeInt, PositiveInt, TypeAdapter

# from phonenumber_field.phonenumber import PhoneNumber
from pydantic_extra_types.phone_numbers import PhoneNumber, PhoneNumberValidator

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

    # for reasons described in the model, BillingInfo.phone_number
    # in nullable, but null values shouldn't be actually allowed,
    # so we force the field to be required
    phone_number: Annotated[PhoneNumber, PhoneNumberValidator(default_region="FR")]
