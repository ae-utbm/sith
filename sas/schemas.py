from datetime import datetime
from pathlib import Path
from typing import Annotated

from django.urls import reverse
from ninja import FilterLookup, FilterSchema, ModelSchema, Schema
from pydantic import Field, NonNegativeInt

from core.schemas import NonEmptyStr, SimpleUserSchema, UserProfileSchema
from sas.models import Album, Picture, PictureModerationRequest


class AlbumFilterSchema(FilterSchema):
    search: Annotated[NonEmptyStr | None, FilterLookup("name__icontains")] = None
    before_date: Annotated[datetime | None, FilterLookup("event_date__lte")] = None
    after_date: Annotated[datetime | None, FilterLookup("event_date__gte")] = None
    parent_id: Annotated[int | None, FilterLookup("parent_id")] = None


class SimpleAlbumSchema(ModelSchema):
    class Meta:
        model = Album
        fields = ["id", "name"]


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
    before_date: Annotated[datetime | None, FilterLookup("date__lte")] = None
    after_date: Annotated[datetime | None, FilterLookup("date__gte")] = None
    users_identified: Annotated[
        set[int] | None, FilterLookup("people__user_id__in")
    ] = None
    album_id: Annotated[int | None, FilterLookup("parent_id")] = None


class PictureSchema(ModelSchema):
    class Meta:
        model = Picture
        fields = ["id", "name", "date", "size", "is_moderated", "asked_for_removal"]

    owner: UserProfileSchema
    sas_url: str
    full_size_url: str
    compressed_url: str
    thumb_url: str
    album: SimpleAlbumSchema = Field(alias="parent")
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
