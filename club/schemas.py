from ninja import ModelSchema

from club.models import Club, Membership
from core.schemas import SimpleUserSchema


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
