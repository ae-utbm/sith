from ninja import ModelSchema

from club.models import Club


class ClubSchema(ModelSchema):
    class Meta:
        model = Club
        fields = ["id", "name"]
