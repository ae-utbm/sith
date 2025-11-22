from datetime import datetime
from typing import Annotated

from ninja import FilterLookup, FilterSchema, ModelSchema
from ninja_extra import service_resolver
from ninja_extra.context import RouteContext

from club.schemas import ClubProfileSchema
from com.models import News, NewsDate
from core.markdown import markdown


class NewsDateFilterSchema(FilterSchema):
    before: Annotated[datetime | None, FilterLookup("end_date__lt")] = None
    after: Annotated[datetime | None, FilterLookup("start_date__gt")] = None
    club_id: Annotated[int | None, FilterLookup("news__club_id")] = None
    news_id: int | None = None
    is_published: Annotated[bool | None, FilterLookup("news__is_published")] = None
    title: Annotated[str | None, FilterLookup("news__title__icontains")] = None


class NewsSchema(ModelSchema):
    class Meta:
        model = News
        fields = ["id", "title", "summary", "is_published"]

    club: ClubProfileSchema
    url: str

    @staticmethod
    def resolve_summary(obj: News) -> str:
        # if this is returned from a route that allows the
        # user to choose the text format (md or html)
        # and the user chose "html", convert the markdown to html
        context: RouteContext = service_resolver(RouteContext)
        if context.kwargs.get("text_format", "") == "html":
            return markdown(obj.summary)
        return obj.summary

    @staticmethod
    def resolve_url(obj: News) -> str:
        return obj.get_absolute_url()


class NewsDateSchema(ModelSchema):
    """Basic infos about an event occurrence.

    Warning:
        This uses [NewsSchema][], which itself
        uses [ClubProfileSchema][club.schemas.ClubProfileSchema].
        Don't forget the appropriated `select_related`.
    """

    class Meta:
        model = NewsDate
        fields = ["id", "start_date", "end_date"]

    news: NewsSchema
