from django.db.models import Prefetch
from ninja import Query
from ninja.security import SessionAuth
from ninja_extra import ControllerBase, api_controller, paginate, route
from ninja_extra.pagination import PageNumberPaginationExtra
from ninja_extra.schemas import PaginatedResponseSchema

from api.auth import ApiKeyAuth
from api.permissions import CanAccessLookup, HasPerm
from club.models import Club, Membership
from club.schemas import ClubSchema, ClubSearchFilterSchema, SimpleClubSchema


@api_controller("/club")
class ClubController(ControllerBase):
    @route.get(
        "/search",
        response=PaginatedResponseSchema[SimpleClubSchema],
        auth=[ApiKeyAuth(), SessionAuth()],
        permissions=[CanAccessLookup],
        url_name="search_club",
    )
    @paginate(PageNumberPaginationExtra, page_size=50)
    def search_club(self, filters: Query[ClubSearchFilterSchema]):
        return filters.filter(Club.objects.all())

    @route.get(
        "/{int:club_id}",
        response=ClubSchema,
        auth=[ApiKeyAuth(), SessionAuth()],
        permissions=[HasPerm("club.view_club")],
        url_name="fetch_club",
    )
    def fetch_club(self, club_id: int):
        prefetch = Prefetch(
            "members", queryset=Membership.objects.ongoing().select_related("user")
        )
        return self.get_object_or_exception(
            Club.objects.prefetch_related(prefetch), id=club_id
        )
