from typing import Literal

from django.http import HttpResponse
from ninja import Query
from ninja_extra import ControllerBase, api_controller, paginate, route
from ninja_extra.pagination import PageNumberPaginationExtra
from ninja_extra.permissions import IsAuthenticated
from ninja_extra.schemas import PaginatedResponseSchema

from com.ics_calendar import IcsCalendar
from com.models import News, NewsDate
from com.schemas import NewsDateFilterSchema, NewsDateSchema
from core.auth.api_permissions import HasPerm
from core.views.files import send_raw_file


@api_controller("/calendar")
class CalendarController(ControllerBase):
    @route.get("/internal.ics", url_name="calendar_internal")
    def calendar_internal(self):
        return send_raw_file(IcsCalendar.get_internal())

    @route.get(
        "/unpublished.ics",
        permissions=[IsAuthenticated],
        url_name="calendar_unpublished",
    )
    def calendar_unpublished(self):
        return HttpResponse(
            IcsCalendar.get_unpublished(self.context.request.user),
            content_type="text/calendar",
        )


@api_controller("/news")
class NewsController(ControllerBase):
    @route.patch(
        "/{int:news_id}/publish",
        permissions=[HasPerm("com.moderate_news")],
        url_name="moderate_news",
    )
    def publish_news(self, news_id: int):
        news = self.get_object_or_exception(News, id=news_id)
        if not news.is_published:
            news.is_published = True
            news.moderator = self.context.request.user
            news.save()

    @route.patch(
        "/{int:news_id}/unpublish",
        permissions=[HasPerm("com.moderate_news")],
        url_name="unpublish_news",
    )
    def unpublish_news(self, news_id: int):
        news = self.get_object_or_exception(News, id=news_id)
        if news.is_published:
            news.is_published = False
            news.moderator = self.context.request.user
            news.save()

    @route.delete(
        "/{int:news_id}",
        permissions=[HasPerm("com.delete_news")],
        url_name="delete_news",
    )
    def delete_news(self, news_id: int):
        news = self.get_object_or_exception(News, id=news_id)
        news.delete()

    @route.get(
        "/date",
        url_name="fetch_news_dates",
        response=PaginatedResponseSchema[NewsDateSchema],
    )
    @paginate(PageNumberPaginationExtra, page_size=50)
    def fetch_news_dates(
        self,
        filters: Query[NewsDateFilterSchema],
        text_format: Literal["md", "html"] = "md",
    ):
        return filters.filter(
            NewsDate.objects.viewable_by(self.context.request.user)
            .order_by("start_date")
            .select_related("news", "news__club")
        )
