from typing import Annotated

from annotated_types import MinLen
from ninja_extra import ControllerBase, api_controller, paginate, route
from ninja_extra.pagination import PageNumberPaginationExtra
from ninja_extra.schemas import PaginatedResponseSchema

from club.models import Club
from club.schemas import ClubSchema
from core.api_permissions import CanAccessLookup


@api_controller("/club")
class ClubController(ControllerBase):
    @route.get(
        "/search",
        response=PaginatedResponseSchema[ClubSchema],
        permissions=[CanAccessLookup],
    )
    @paginate(PageNumberPaginationExtra, page_size=50)
    def search_club(self, search: Annotated[str, MinLen(1)]):
        return Club.objects.filter(name__icontains=search).values()
