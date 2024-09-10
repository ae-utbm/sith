from django.contrib.staticfiles.storage import staticfiles_storage
from ninja import ModelSchema, Schema

from core.models import User


class SimpleUserSchema(ModelSchema):
    """A schema with the minimum amount of information to represent a user."""

    class Meta:
        model = User
        fields = ["id", "nick_name", "first_name", "last_name"]


class MarkdownSchema(Schema):
    text: str


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


class FamilyGodfatherSchema(Schema):
    godfather: int
    godchild: int


class UserFamilySchema(Schema):
    """Represent a graph of a user's family"""

    users: list[UserProfileSchema]
    relationships: list[FamilyGodfatherSchema]
