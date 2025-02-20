from datetime import datetime
from pathlib import Path
from typing import Annotated

from annotated_types import MinLen
from django.urls import reverse
from ninja import FilterSchema, ModelSchema, Schema
from pydantic import Field, NonNegativeInt

from core.schemas import SimpleUserSchema, UserProfileSchema
from sas.models import Album, Picture, PictureModerationRequest


class AlbumFilterSchema(FilterSchema):
    search: Annotated[str, MinLen(1)] | None = Field(None, q="name__icontains")
    before_date: datetime | None = Field(None, q="event_date__lte")
    after_date: datetime | None = Field(None, q="event_date__gte")
    parent_id: int | None = Field(None, q="parent_id")


class AlbumSchema(ModelSchema):
    class Meta:
        model = Album
        fields = ["id", "name", "is_moderated"]

    thumbnail: str | None
    sas_url: str

    @staticmethod
    def resolve_thumbnail(obj: Album) -> str | None:
        # Album thumbnails aren't stored in `Album.thumbnail` but in `Album.file`
        # Don't ask me why.
        if not obj.file:
            return None
        return obj.get_download_url()

    @staticmethod
    def resolve_sas_url(obj: Album) -> str:
        return obj.get_absolute_url()


class AlbumAutocompleteSchema(ModelSchema):
    """Schema to use on album autocomplete input field."""

    class Meta:
        model = Album
        fields = ["id", "name"]

    path: str

    @staticmethod
    def resolve_path(obj: Album) -> str:
        return str(Path(obj.get_parent_path()) / obj.name)


class PictureFilterSchema(FilterSchema):
    before_date: datetime | None = Field(None, q="date__lte")
    after_date: datetime | None = Field(None, q="date__gte")
    users_identified: set[int] | None = Field(None, q="people__user_id__in")
    album_id: int | None = Field(None, q="parent_id")


class PictureSchema(ModelSchema):
    class Meta:
        model = Picture
        fields = ["id", "name", "date", "size", "is_moderated", "asked_for_removal"]

    owner: UserProfileSchema
    sas_url: str
    full_size_url: str
    compressed_url: str
    thumb_url: str
    album: str
    report_url: str
    edit_url: str

    @staticmethod
    def resolve_sas_url(obj: Picture) -> str:
        return reverse("sas:picture", kwargs={"picture_id": obj.id})

    @staticmethod
    def resolve_full_size_url(obj: Picture) -> str:
        return obj.get_download_url()

    @staticmethod
    def resolve_compressed_url(obj: Picture) -> str:
        return obj.get_download_compressed_url()

    @staticmethod
    def resolve_thumb_url(obj: Picture) -> str:
        return obj.get_download_thumb_url()

    @staticmethod
    def resolve_report_url(obj: Picture) -> str:
        return reverse("sas:picture_ask_removal", kwargs={"picture_id": obj.id})

    @staticmethod
    def resolve_edit_url(obj: Picture) -> str:
        return reverse("sas:picture_edit", kwargs={"picture_id": obj.id})


class PictureRelationCreationSchema(Schema):
    picture: NonNegativeInt
    users: list[NonNegativeInt]


class IdentifiedUserSchema(Schema):
    id: int
    user: UserProfileSchema


class ModerationRequestSchema(ModelSchema):
    author: SimpleUserSchema

    class Meta:
        model = PictureModerationRequest
        fields = ["id", "created_at", "reason"]
