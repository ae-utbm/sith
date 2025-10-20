from typing import Annotated, Optional

from annotated_types import MinLen
from django.db.models import Q
from ninja import Field, FilterSchema, ModelSchema

from club.models import Club, Membership
from core.schemas import SimpleUserSchema


class ClubSearchFilterSchema(FilterSchema):
    search: Annotated[str, MinLen(1)] | None = Field(None, q="name__icontains")
    is_active: bool | None = None
    parent_id: int | None = None
    parent_name: str | None = Field(None, q="parent__name__icontains")
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
        fields = ["id", "name", "logo"]

    url: str

    @staticmethod
    def resolve_url(obj: Club) -> str:
        return obj.get_absolute_url()


class ClubMemberSchema(ModelSchema):
    class Meta:
        model = Membership
        fields = ["start_date", "end_date", "role", "description"]

    user: SimpleUserSchema


class ClubSchema(ModelSchema):
    class Meta:
        model = Club
        fields = ["id", "name", "logo", "is_active", "short_description", "address"]

    members: list[ClubMemberSchema]
