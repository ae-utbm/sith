from typing import Annotated

import annotated_types
from django.conf import settings
from django.http import HttpResponse
from ninja import Query
from ninja_extra import ControllerBase, api_controller, paginate, route
from ninja_extra.exceptions import PermissionDenied
from ninja_extra.pagination import PageNumberPaginationExtra
from ninja_extra.schemas import PaginatedResponseSchema

from club.models import Mailing
from core.api_permissions import CanView, IsLoggedInCounter, IsOldSubscriber, IsRoot
from core.models import User
from core.schemas import (
    FamilyGodfatherSchema,
    MarkdownSchema,
    UserFamilySchema,
    UserFilterSchema,
    UserProfileSchema,
)
from core.templatetags.renderer import markdown


@api_controller("/markdown")
class MarkdownController(ControllerBase):
    @route.post("", url_name="markdown")
    def render_markdown(self, body: MarkdownSchema):
        """Convert the markdown text into html."""
        return HttpResponse(markdown(body.text), content_type="text/html")


@api_controller("/mailings")
class MailingListController(ControllerBase):
    @route.get("", response=str)
    def fetch_mailing_lists(self, key: str):
        if key != settings.SITH_MAILING_FETCH_KEY:
            raise PermissionDenied
        mailings = Mailing.objects.filter(
            is_moderated=True, club__is_active=True
        ).prefetch_related("subscriptions")
        data = "\n".join(m.fetch_format() for m in mailings)
        return data


@api_controller("/user", permissions=[IsOldSubscriber | IsRoot | IsLoggedInCounter])
class UserController(ControllerBase):
    @route.get("", response=list[UserProfileSchema])
    def fetch_profiles(self, pks: Query[set[int]]):
        return User.objects.filter(pk__in=pks)

    @route.get("/search", response=PaginatedResponseSchema[UserProfileSchema])
    @paginate(PageNumberPaginationExtra, page_size=20)
    def search_users(self, filters: Query[UserFilterSchema]):
        return filters.filter(User.objects.all())


DepthValue = Annotated[int, annotated_types.Ge(0), annotated_types.Le(10)]
DEFAULT_DEPTH = 4


@api_controller("/family")
class FamilyController(ControllerBase):
    @route.get(
        "/{user_id}",
        permissions=[CanView],
        response=UserFamilySchema,
        url_name="family_graph",
    )
    def get_family_graph(
        self,
        user_id: int,
        godfathers_depth: DepthValue = DEFAULT_DEPTH,
        godchildren_depth: DepthValue = DEFAULT_DEPTH,
    ):
        user: User = self.get_object_or_exception(User, pk=user_id)

        relations = user.get_family(godfathers_depth, godchildren_depth)
        if not relations:
            # If the user has no relations, return only the user
            # He is alone in its family, but the family exists nonetheless
            return {"users": [user], "relationships": []}

        user_ids = {r.from_user_id for r in relations} | {
            r.to_user_id for r in relations
        }
        return {
            "users": User.objects.filter(id__in=user_ids).distinct(),
            "relationships": (
                [
                    FamilyGodfatherSchema(
                        godchild=r.from_user_id, godfather=r.to_user_id
                    )
                    for r in relations
                ]
            ),
        }
