from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.http import Http404
from django.urls import reverse
from django.utils import timezone
from ics import Calendar, Event
from ninja_extra import ControllerBase, api_controller, route

from com.models import IcsCalendar, NewsDate
from core.views.files import send_raw_file


@api_controller("/calendar")
class CalendarController(ControllerBase):
    CACHE_FOLDER: Path = settings.MEDIA_ROOT / "com" / "calendars"

    @route.get("/external.ics")
    def calendar_external(self):
        """Return the ICS file of the AE Google Calendar

        Because of Google's cors rules, we can't "just" do a request to google ics
        from the frontend. Google is blocking CORS request in it's responses headers.
        The only way to do it from the frontend is to use Google Calendar API with an API key
        This is not especially desirable as your API key is going to be provided to the frontend.

        This is why we have this backend based solution.
        """
        if (calendar := IcsCalendar.get_external()) is not None:
            return send_raw_file(calendar)
        raise Http404

    @route.get("/internal.ics")
    def calendar_internal(self):
        calendar = Calendar()
        for news_date in NewsDate.objects.filter(
            news__is_moderated=True,
            end_date__gte=timezone.now()
            - (timedelta(days=30) * 60),  # Roughly get the last 6 months
        ).prefetch_related("news"):
            event = Event(
                name=news_date.news.title,
                begin=news_date.start_date,
                end=news_date.end_date,
                url=reverse("com:news_detail", kwargs={"news_id": news_date.news.id}),
            )
            calendar.events.add(event)

        # Create a file so we can offload the download to the reverse proxy if available
        file = self.CACHE_FOLDER / "internal.ics"
        self.CACHE_FOLDER.mkdir(parents=True, exist_ok=True)
        with open(file, "wb") as f:
            _ = f.write(calendar.serialize().encode("utf-8"))
        return send_raw_file(file)
