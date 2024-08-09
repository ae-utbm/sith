from datetime import datetime

from ninja import FilterSchema, ModelSchema, Schema
from pydantic import Field, NonNegativeInt

from sas.models import PeoplePictureRelation, Picture


class PictureFilterSchema(FilterSchema):
    before_date: datetime | None = Field(None, q="date__lte")
    after_date: datetime | None = Field(None, q="date__gte")
    users_identified: set[int] | None = Field(None, q="people__user_id__in")
    album_id: int | None = Field(None, q="parent_id")


class PictureSchema(ModelSchema):
    class Meta:
        model = Picture
        fields = ["id", "name", "date", "size", "is_moderated"]

    full_size_url: str
    compressed_url: str
    thumb_url: str
    album: str

    @staticmethod
    def resolve_full_size_url(obj: Picture) -> str:
        return obj.get_download_url()

    @staticmethod
    def resolve_compressed_url(obj: Picture) -> str:
        return obj.get_download_compressed_url()

    @staticmethod
    def resolve_thumb_url(obj: Picture) -> str:
        return obj.get_download_thumb_url()


class PictureCreateRelationSchema(Schema):
    user_id: NonNegativeInt
    picture_id: NonNegativeInt


class CreatedPictureRelationSchema(ModelSchema):
    class Meta:
        model = PeoplePictureRelation
        fields = ["id", "user", "picture"]
