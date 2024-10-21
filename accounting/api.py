from typing import Annotated

from annotated_types import MinLen
from ninja_extra import ControllerBase, api_controller, paginate, route
from ninja_extra.pagination import PageNumberPaginationExtra
from ninja_extra.schemas import PaginatedResponseSchema

from accounting.models import ClubAccount, Company
from accounting.schemas import ClubAccountSchema, CompanySchema
from core.api_permissions import CanAccessLookup


@api_controller("/lookup", permissions=[CanAccessLookup])
class AccountingController(ControllerBase):
    @route.get("/club-account", response=PaginatedResponseSchema[ClubAccountSchema])
    @paginate(PageNumberPaginationExtra, page_size=50)
    def search_club_account(self, search: Annotated[str, MinLen(1)]):
        return ClubAccount.objects.filter(name__icontains=search).values()

    @route.get("/company", response=PaginatedResponseSchema[CompanySchema])
    @paginate(PageNumberPaginationExtra, page_size=50)
    def search_company(self, search: Annotated[str, MinLen(1)]):
        return Company.objects.filter(name__icontains=search).values()
