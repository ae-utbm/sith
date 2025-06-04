import operator
from typing import Annotated

from annotated_types import Ge
from ninja import Query
from ninja.security import SessionAuth
from ninja_extra import ControllerBase, api_controller, paginate, route
from ninja_extra.exceptions import NotFound
from ninja_extra.pagination import PageNumberPaginationExtra, PaginatedResponseSchema

from api.auth import ApiKeyAuth
from api.permissions import HasPerm
from pedagogy.models import UV
from pedagogy.schemas import SimpleUvSchema, UvFilterSchema, UvSchema
from pedagogy.utbm_api import UtbmApiClient


@api_controller("/uv")
class UvController(ControllerBase):
    @route.get(
        "/{code}",
        auth=[SessionAuth(), ApiKeyAuth()],
        permissions=[
            # this route will almost always be called in the context
            # of a UV creation/edition
            HasPerm(["pedagogy.add_uv", "pedagogy.change_uv"], op=operator.or_)
        ],
        url_name="fetch_uv_from_utbm",
        response=UvSchema,
    )
    def fetch_from_utbm_api(
        self,
        code: str,
        lang: Query[str] = "fr",
        year: Query[Annotated[int, Ge(2010)] | None] = None,
    ):
        """Fetch UV data from the UTBM API and returns it after some parsing."""
        with UtbmApiClient() as client:
            res = client.find_uv(lang, code, year)
        if res is None:
            raise NotFound
        return res

    @route.get(
        "",
        response=PaginatedResponseSchema[SimpleUvSchema],
        url_name="fetch_uvs",
        auth=[SessionAuth(), ApiKeyAuth()],
        permissions=[HasPerm("pedagogy.view_uv")],
    )
    @paginate(PageNumberPaginationExtra, page_size=100)
    def fetch_uv_list(self, search: Query[UvFilterSchema]):
        return search.filter(UV.objects.order_by("code").values())
