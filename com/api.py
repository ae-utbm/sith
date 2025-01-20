from pathlib import Path

from django.conf import settings
from django.http import Http404
from ninja_extra import ControllerBase, api_controller, route

from com.calendar import IcsCalendar
from com.models import News
from core.auth.api_permissions import HasPerm
from core.views.files import send_raw_file


@api_controller("/calendar")
class CalendarController(ControllerBase):
    CACHE_FOLDER: Path = settings.MEDIA_ROOT / "com" / "calendars"

    @route.get("/external.ics", url_name="calendar_external")
    def calendar_external(self):
        """Return the ICS file of the AE Google Calendar

        Because of Google's cors rules, we can't just do a request to google ics
        from the frontend. Google is blocking CORS request in its responses headers.
        The only way to do it from the frontend is to use Google Calendar API with an API key
        This is not especially desirable as your API key is going to be provided to the frontend.

        This is why we have this backend based solution.
        """
        if (calendar := IcsCalendar.get_external()) is not None:
            return send_raw_file(calendar)
        raise Http404

    @route.get("/internal.ics", url_name="calendar_internal")
    def calendar_internal(self):
        return send_raw_file(IcsCalendar.get_internal())


@api_controller("/news")
class NewsController(ControllerBase):
    @route.patch(
        "/{news_id}/moderate",
        permissions=[HasPerm("com.moderate_news")],
        url_name="moderate_news",
    )
    def moderate_news(self, news_id: int):
        news = self.get_object_or_exception(News, id=news_id)
        if not news.is_moderated:
            news.is_moderated = True
            news.save()

    @route.delete(
        "/{news_id}",
        permissions=[HasPerm("com.delete_news")],
        url_name="delete_news",
    )
    def delete_news(self, news_id: int):
        news = self.get_object_or_exception(News, id=news_id)
        news.delete()
