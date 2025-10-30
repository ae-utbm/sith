from ninja import ModelSchema, Schema
from pydantic import Field, HttpUrl

from api.models import ApiClient
from core.schemas import SimpleUserSchema


class ApiClientSchema(ModelSchema):
    class Meta:
        model = ApiClient
        fields = ["id", "name"]

    owner: SimpleUserSchema
    permissions: list[str] = Field(alias="all_permissions")


class ThirdPartyAuthParamsSchema(Schema):
    client_id: int
    third_party_app: str
    privacy_link: HttpUrl
    username: str
    callback_url: HttpUrl
    signature: str
