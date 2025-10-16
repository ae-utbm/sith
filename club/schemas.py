from typing import Optional

from django.db.models import Q
from ninja import Field, FilterSchema, ModelSchema

from club.models import Club, Membership
from core.schemas import SimpleUserSchema


class ClubSearchFilterSchema(FilterSchema):
    search: Optional[str] = Field(None, q="name__icontains")
    club_id: Optional[int] = Field(None, q="id")
    is_active: Optional[bool] = None
    parent_id: Optional[int] = None
    parent_name: Optional[str] = Field(None, q="parent__name__icontains")
    exclude_ids: Optional[list[int]] = None

    def filter_exclude_ids(self, value: list[int]):
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
