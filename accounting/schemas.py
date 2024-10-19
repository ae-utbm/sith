from ninja import ModelSchema

from accounting.models import ClubAccount, Company


class ClubAccountSchema(ModelSchema):
    class Meta:
        model = ClubAccount
        fields = ["id", "name"]


class CompanySchema(ModelSchema):
    class Meta:
        model = Company
        fields = ["id", "name"]
