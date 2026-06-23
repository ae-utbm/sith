from django.db.models import Prefetch
from ninja import Query
from ninja.security import SessionAuth
from ninja_extra import ControllerBase, api_controller, paginate, route
from ninja_extra.pagination import PageNumberPaginationExtra
from ninja_extra.schemas import PaginatedResponseSchema

from api.auth import ApiKeyAuth
from api.permissions import CanView, HasPerm
from club.models import Club, Membership
from club.schemas import (
    ClubSchema,
    ClubSearchFilterSchema,
    MembershipFilterSchema,
    SimpleClubSchema,
    UserMembershipSchema,
)
from core.models import User


@api_controller("/club")
class ClubController(ControllerBase):
    @route.get(
        "/search",
        response=PaginatedResponseSchema[SimpleClubSchema],
        url_name="search_club",
    )
    @paginate(PageNumberPaginationExtra, page_size=50)
    def search_club(self, filters: Query[ClubSearchFilterSchema]):
        return filters.filter(Club.objects.order_by("name")).values()

    @route.get(
        "/{int:club_id}",
        response=ClubSchema,
        auth=[ApiKeyAuth(), SessionAuth()],
        permissions=[HasPerm("club.view_club")],
        url_name="fetch_club",
    )
    def fetch_club(self, club_id: int):
        prefetch = Prefetch(
            "members",
            queryset=Membership.objects.ongoing().select_related("user", "role"),
        )
        return self.get_object_or_exception(
            Club.objects.prefetch_related(prefetch, "links"), id=club_id
        )


@api_controller("/user/{int:user_id}/club")
class UserClubController(ControllerBase):
    @route.get(
        "",
        response=list[UserMembershipSchema],
        auth=[ApiKeyAuth(), SessionAuth()],
        permissions=[CanView],
        url_name="fetch_user_clubs",
    )
    def fetch_user_clubs(self, user_id: int):
        """Get all the active memberships of the given user."""
        user = self.get_object_or_exception(User, id=user_id)
        return (
            Membership.objects.ongoing()
            .filter(user=user)
            .select_related("club", "user", "role")
        )


@api_controller("/clubs/members/")
class ClubMembershipController(ControllerBase):
    @route.get(
        "/new",
        response=list[UserMembershipSchema],
        auth=[ApiKeyAuth(), SessionAuth()],
        permissions=[HasPerm("club.view_club")],
        url_name="get_new_clubs_members_since_date",
    )
    def fetch_new_club_members(self, filters: Query[MembershipFilterSchema]):
        """give all the members of all clubs that have joined since a given date"""
        memberships = (
            Membership.objects.ongoing()
            .filter(start_date__gte=filters.since_date, end_date__isnull=True)
            .select_related("user", "role")
        )
        if filters.clubs_id:
            memberships = memberships.filter(club_id__in=filters.clubs_id)

        return memberships.order_by("start_date")

    @route.get(
        "/former",
        response=list[UserMembershipSchema],
        auth=[ApiKeyAuth(), SessionAuth()],
        permissions=[HasPerm("club.view_club")],
        url_name="get_former_clubs_members_since_date",
    )
    def fetch_former_club_members(self, filters: Query[MembershipFilterSchema]):
        """give all the former members of all clubs that have left since a given date"""
        memberships = Membership.objects.filter(
            start_date__lt=filters.since_date,
            end_date__gte=filters.since_date,
        ).select_related("user", "role")
        if filters.clubs_id:
            memberships = memberships.filter(club_id__in=filters.clubs_id)

        return memberships.order_by("start_date")
