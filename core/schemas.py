from pathlib import Path
from typing import Annotated, Any

from annotated_types import MinLen
from django.contrib.staticfiles.storage import staticfiles_storage
from django.db.models import Q
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext as _
from haystack.query import SearchQuerySet
from ninja import FilterSchema, ModelSchema, Schema, UploadedFile
from pydantic import AliasChoices, Field
from pydantic_core.core_schema import ValidationInfo

from core.models import Group, QuickUploadImage, SithFile, User
from core.utils import is_image


class UploadedImage(UploadedFile):
    @classmethod
    def _validate(cls, v: Any, info: ValidationInfo) -> Any:
        super()._validate(v, info)
        if not is_image(v):
            msg = _("This file is not a valid image")
            raise ValueError(msg)
        return v


class SimpleUserSchema(ModelSchema):
    """A schema with the minimum amount of information to represent a user."""

    class Meta:
        model = User
        fields = ["id", "nick_name", "first_name", "last_name"]


class UserProfileSchema(ModelSchema):
    """The necessary information to show a user profile"""

    class Meta:
        model = User
        fields = ["id", "nick_name", "first_name", "last_name"]

    display_name: str
    profile_url: str
    profile_pict: str

    @staticmethod
    def resolve_display_name(obj: User) -> str:
        return obj.get_display_name()

    @staticmethod
    def resolve_profile_url(obj: User) -> str:
        return reverse("core:user_profile", kwargs={"user_id": obj.pk})

    @staticmethod
    def resolve_profile_pict(obj: User) -> str:
        if obj.profile_pict_id is None:
            return staticfiles_storage.url("core/img/unknown.jpg")
        return reverse("core:download", kwargs={"file_id": obj.profile_pict_id})


class UploadedFileSchema(ModelSchema):
    class Meta:
        model = QuickUploadImage
        fields = ["uuid", "name", "width", "height", "size"]

    href: str

    @staticmethod
    def resolve_href(obj: QuickUploadImage) -> str:
        return obj.get_absolute_url()


class SithFileSchema(ModelSchema):
    class Meta:
        model = SithFile
        fields = ["id", "name"]

    path: str

    @staticmethod
    def resolve_path(obj: SithFile) -> str:
        return str(Path(obj.get_parent_path()) / obj.name)


class GroupSchema(ModelSchema):
    class Meta:
        model = Group
        fields = ["id", "name"]


class UserFilterSchema(FilterSchema):
    search: Annotated[str, MinLen(1)]
    exclude: list[int] | None = Field(
        None, validation_alias=AliasChoices("exclude", "exclude[]")
    )

    def filter_search(self, value: str | None) -> Q:
        if not value:
            return Q()
        if len(value) < 3:
            # For small queries, full text search isn't necessary
            return (
                Q(first_name__istartswith=value)
                | Q(last_name__istartswith=value)
                | Q(nick_name__istartswith=value)
            )
        return Q(
            id__in=list(
                SearchQuerySet()
                .models(User)
                .autocomplete(auto=slugify(value).replace("-", " "))
                .values_list("pk", flat=True)
            )
        )

    def filter_exclude(self, value: set[int] | None) -> Q:
        if not value:
            return Q()
        return ~Q(id__in=value)


class MarkdownSchema(Schema):
    text: str


class FamilyGodfatherSchema(Schema):
    godfather: int
    godchild: int


class UserFamilySchema(Schema):
    """Represent a graph of a user's family"""

    users: list[UserProfileSchema]
    relationships: list[FamilyGodfatherSchema]
