from ninja import ModelSchema

from club.models import Club


class ClubSchema(ModelSchema):
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
