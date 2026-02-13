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
from pedagogy.models import UE
from pedagogy.schemas import SimpleUeSchema, UeFilterSchema, UeSchema
from pedagogy.utbm_api import UtbmApiClient


@api_controller("/ue")
class UeController(ControllerBase):
    @route.get(
        "/{code}",
        auth=[ApiKeyAuth(), SessionAuth()],
        permissions=[
            # this route will almost always be called in the context
            # of a UE creation/edition
            HasPerm(["pedagogy.add_ue", "pedagogy.change_ue"], op=operator.or_)
        ],
        url_name="fetch_ue_from_utbm",
        response=UeSchema,
    )
    def fetch_from_utbm_api(
        self,
        code: str,
        lang: Query[str] = "fr",
        year: Query[Annotated[int, Ge(2010)] | None] = None,
    ):
        """Fetch UE data from the UTBM API and returns it after some parsing."""
        with UtbmApiClient() as client:
            res = client.find_ue(lang, code, year)
        if res is None:
            raise NotFound
        return res

    @route.get(
        "",
        response=PaginatedResponseSchema[SimpleUeSchema],
        url_name="fetch_ues",
        auth=[ApiKeyAuth(), SessionAuth()],
        permissions=[HasPerm("pedagogy.view_ue")],
    )
    @paginate(PageNumberPaginationExtra, page_size=100)
    def fetch_ue_list(self, search: Query[UeFilterSchema]):
        return search.filter(UE.objects.order_by("code"))
