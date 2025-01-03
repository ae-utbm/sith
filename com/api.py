from datetime import datetime, timedelta
from pathlib import Path

import urllib3
from django.conf import settings
from django.http import HttpResponse
from django.urls import reverse
from django.utils import timezone
from ics import Calendar, Event
from ninja_extra import ControllerBase, api_controller, route

from com.models import NewsDate
from core.views.files import send_raw_file


@api_controller("/calendar")
class CalendarController(ControllerBase):
    CACHE_FOLDER: Path = settings.MEDIA_ROOT / "com" / "calendars"

    @route.get("/external.ics")
    def calendar_external(self):
        file = self.CACHE_FOLDER / "external.ics"
        # Return cached file if updated less than an our ago
        if (
            file.exists()
            and timezone.make_aware(datetime.fromtimestamp(file.stat().st_mtime))
            + timedelta(hours=1)
            > timezone.now()
        ):
            return send_raw_file(file)

        calendar = urllib3.request(
            "GET",
            "https://calendar.google.com/calendar/ical/ae.utbm%40gmail.com/public/basic.ics",
        )
        if calendar.status != 200:
            return HttpResponse(status=calendar.status)

        self.CACHE_FOLDER.mkdir(parents=True, exist_ok=True)
        with open(file, "wb") as f:
            _ = f.write(calendar.data)

        return send_raw_file(file)

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
