from typing import Annotated

from annotated_types import MinLen
from ninja.security import SessionAuth
from ninja_extra import ControllerBase, api_controller, paginate, route
from ninja_extra.pagination import PageNumberPaginationExtra
from ninja_extra.schemas import PaginatedResponseSchema

from apikey.auth import ApiKeyAuth
from club.models import Club
from club.schemas import ClubSchema, SimpleClubSchema
from core.auth.api_permissions import CanAccessLookup, HasPerm


@api_controller("/club")
class ClubController(ControllerBase):
    @route.get(
        "/search",
        response=PaginatedResponseSchema[SimpleClubSchema],
        auth=[SessionAuth(), ApiKeyAuth()],
        permissions=[CanAccessLookup],
        url_name="search_club",
    )
    @paginate(PageNumberPaginationExtra, page_size=50)
    def search_club(self, search: Annotated[str, MinLen(1)]):
        return Club.objects.filter(name__icontains=search).values()

    @route.get(
        "/{int:club_id}",
        response=ClubSchema,
        auth=[SessionAuth(), ApiKeyAuth()],
        permissions=[HasPerm("club.view_club")],
        url_name="fetch_club",
    )
    def fetch_club(self, club_id: int):
        return self.get_object_or_exception(
            Club.objects.prefetch_related("members", "members__user"), id=club_id
        )
