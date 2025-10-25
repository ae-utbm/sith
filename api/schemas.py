from ninja import ModelSchema
from pydantic import Field

from api.models import ApiClient
from core.schemas import SimpleUserSchema


class ApiClientSchema(ModelSchema):
    class Meta:
        model = ApiClient
        fields = ["id", "name"]

    owner: SimpleUserSchema
    permissions: list[str] = Field(alias="all_permissions")
