from typing import Annotated

from annotated_types import Ge
from django.conf import settings
from ninja import Query
from ninja_extra import ControllerBase, api_controller, paginate, route
from ninja_extra.exceptions import NotFound
from ninja_extra.pagination import PageNumberPaginationExtra, PaginatedResponseSchema

from core.auth.api_permissions import IsInGroup, IsRoot, IsSubscriber
from pedagogy.models import UV
from pedagogy.schemas import SimpleUvSchema, UvFilterSchema, UvSchema
from pedagogy.utbm_api import find_uv


@api_controller("/uv")
class UvController(ControllerBase):
    @route.get(
        "/{year}/{code}",
        permissions=[IsRoot | IsInGroup(settings.SITH_GROUP_PEDAGOGY_ADMIN_ID)],
        url_name="fetch_uv_from_utbm",
        response=UvSchema,
    )
    def fetch_from_utbm_api(
        self, year: Annotated[int, Ge(2010)], code: str, lang: Query[str] = "fr"
    ):
        """Fetch UV data from the UTBM API and returns it after some parsing."""
        res = find_uv(lang, year, code)
        if res is None:
            raise NotFound
        return res

    @route.get(
        "",
        response=PaginatedResponseSchema[SimpleUvSchema],
        url_name="fetch_uvs",
        permissions=[IsSubscriber | IsInGroup(settings.SITH_GROUP_PEDAGOGY_ADMIN_ID)],
    )
    @paginate(PageNumberPaginationExtra, page_size=100)
    def fetch_uv_list(self, search: Query[UvFilterSchema]):
        return search.filter(UV.objects.all())
