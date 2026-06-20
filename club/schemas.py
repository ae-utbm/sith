from datetime import datetime
from typing import Annotated

from django.db.models import Q
from ninja import FilterLookup, FilterSchema, ModelSchema
from pydantic import HttpUrl

from club.models import Club, ClubRole, Membership
from core.schemas import NonEmptyStr, SimpleUserSchema


class ClubSearchFilterSchema(FilterSchema):
    search: Annotated[NonEmptyStr | None, FilterLookup("name__icontains")] = None
    is_active: bool | None = None
    parent_id: int | None = None
    exclude_ids: set[int] | None = None

    def filter_exclude_ids(self, value: set[int] | None):
        if value is None:
            return Q()
        return ~Q(id__in=value)


class SimpleClubSchema(ModelSchema):
    class Meta:
        model = Club
        fields = ["id", "name"]


class ClubProfileSchema(ModelSchema):
    """The infos needed to display a simple club profile."""

    class Meta:
        model = Club
        fields = ["id", "name", "logo", "is_active", "short_description"]

    url: str

    @staticmethod
    def resolve_url(obj: Club) -> str:
        return obj.get_absolute_url()


class ClubRoleSchema(ModelSchema):
    class Meta:
        model = ClubRole
        fields = ["id", "name", "is_presidency", "is_board"]


class ClubMemberSchema(ModelSchema):
    """A schema to represent all memberships in a club."""

    class Meta:
        model = Membership
        fields = ["start_date", "end_date", "description"]

    user: SimpleUserSchema
    role: ClubRoleSchema


class ClubSchema(ModelSchema):
    class Meta:
        model = Club
        fields = ["id", "name", "logo", "is_active", "short_description", "address"]

    members: list[ClubMemberSchema]
    links: list[HttpUrl]

    @staticmethod
    def resolve_links(obj: Club):
        return [link.url for link in obj.links.all()]


class UserMembershipSchema(ModelSchema):
    """A schema to represent the active club memberships of a user."""

    class Meta:
        model = Membership
        fields = ["id", "start_date", "description"]

    club: SimpleClubSchema
    role: ClubRoleSchema
    user: SimpleUserSchema


class MembershipFilterSchema(FilterSchema):
    since_date: Annotated[datetime, FilterLookup("date__lte")]
    clubs_id: set[int] | None = None
