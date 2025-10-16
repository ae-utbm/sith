from typing import Annotated, Optional

from annotated_types import MinLen
from django.db.models import Prefetch
from ninja.security import SessionAuth
from ninja_extra import ControllerBase, api_controller, paginate, route
from ninja_extra.pagination import PageNumberPaginationExtra
from ninja_extra.schemas import PaginatedResponseSchema

from api.auth import ApiKeyAuth
from api.permissions import CanAccessLookup, HasPerm
from club.models import Club, Membership
from club.schemas import ClubSchema, SimpleClubSchema


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
    def search_club(
        self,
        search: Annotated[Optional[str], MinLen(1), "filter by name"] = None,
        club_id: Annotated[Optional[int], "filter by club id"] = None,
        excluded_ids: Annotated[
            Optional[list[int]], "filter by excluded club ids"
        ] = None,
        is_active: Annotated[Optional[bool], "filter by club activity"] = None,
        parent_id: Annotated[Optional[int], "filter by parent id"] = None,
        parent_name: Annotated[
            Optional[str], MinLen(1), "filter by parent name"
        ] = None,
    ):
        queryset = Club.objects.all()

        if search:
            queryset = queryset.filter(name__icontains=search)
        if club_id:
            queryset = queryset.filter(id=club_id)
        if is_active:
            queryset = queryset.filter(is_active=is_active)
        if parent_name:
            queryset = queryset.filter(parent__name__icontains=parent_name)
        if parent_id:
            queryset = queryset.filter(parent_id=parent_id)
        if excluded_ids:
            queryset = queryset.exclude(id__in=excluded_ids)

        return queryset.values()

    @route.get(
        "/{int:club_id}",
        response=ClubSchema,
        auth=[SessionAuth(), ApiKeyAuth()],
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
