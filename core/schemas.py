from typing import Annotated

from annotated_types import MinLen
from django.contrib.staticfiles.storage import staticfiles_storage
from django.db.models import Q
from django.utils.text import slugify
from haystack.query import SearchQuerySet
from ninja import FilterSchema, ModelSchema, Schema
from pydantic import AliasChoices, Field

from core.models import User


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
        return obj.get_absolute_url()

    @staticmethod
    def resolve_profile_pict(obj: User) -> str:
        if obj.profile_pict_id is None:
            return staticfiles_storage.url("core/img/unknown.jpg")
        return obj.profile_pict.get_download_url()


class UserFilterSchema(FilterSchema):
    search: Annotated[str, MinLen(1)]
    exclude: list[int] | None = Field(
        None, validation_alias=AliasChoices("exclude", "exclude[]")
    )

    def filter_search(self, value: str | None) -> Q:
        if not value:
            return Q()
        if len(value) < 4:
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
                .order_by("-last_update")
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
