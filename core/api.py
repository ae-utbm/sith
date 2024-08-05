from django.conf import settings
from django.http import HttpResponse
from ninja import Query
from ninja_extra import ControllerBase, api_controller, paginate, route
from ninja_extra.exceptions import PermissionDenied
from ninja_extra.pagination import PageNumberPaginationExtra
from ninja_extra.schemas import PaginatedResponseSchema

from club.models import Mailing
from core.api_permissions import IsLoggedInCounter, IsOldSubscriber, IsRoot
from core.models import User
from core.schemas import MarkdownSchema, UserFilterSchema, UserProfileSchema
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

    @route.get(
        "/search",
        response=PaginatedResponseSchema[UserProfileSchema],
        url_name="search_users",
    )
    @paginate(PageNumberPaginationExtra, page_size=20)
    def search_users(self, filters: Query[UserFilterSchema]):
        return filters.filter(User.objects.all())
