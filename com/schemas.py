from datetime import datetime

from ninja import FilterSchema, ModelSchema
from ninja_extra import service_resolver
from ninja_extra.controllers import RouteContext
from pydantic import Field

from club.schemas import ClubProfileSchema
from com.models import News, NewsDate
from core.markdown import markdown


class NewsDateFilterSchema(FilterSchema):
    before: datetime | None = Field(None, q="end_date__lt")
    after: datetime | None = Field(None, q="start_date__gt")
    club_id: int | None = Field(None, q="news__club_id")
    news_id: int | None = None
    is_published: bool | None = Field(None, q="news__is_published")
    title: str | None = Field(None, q="news__title__icontains")


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
