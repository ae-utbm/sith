from typing import Annotated

from django.db.models import Q
from ninja import FilterLookup, FilterSchema, ModelSchema

from club.models import Club, Membership
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
