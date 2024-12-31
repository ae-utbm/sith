from datetime import timedelta

import urllib3
from django.core.cache import cache
from django.http import HttpResponse
from django.urls import reverse
from django.utils import timezone
from ics import Calendar, Event
from ninja_extra import ControllerBase, api_controller, route

from com.models import NewsDate


@api_controller("/calendar")
class CalendarController(ControllerBase):
    @route.get("/external.ics")
    def calendar_external(self):
        CACHE_KEY = "external_calendar"
        if cached := cache.get(CACHE_KEY):
            return HttpResponse(
                cached,
                content_type="text/calendar",
                status=200,
            )
        calendar = urllib3.request(
            "GET",
            "https://calendar.google.com/calendar/ical/ae.utbm%40gmail.com/public/basic.ics",
        )
        if calendar.status == 200:
            cache.set(CACHE_KEY, calendar.data, 3600)  # Cache for one hour
        return HttpResponse(
            calendar.data,
            content_type="text/calendar",
            status=calendar.status,
        )

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

        return HttpResponse(
            calendar.serialize().encode("utf-8"),
            content_type="text/calendar",
        )
