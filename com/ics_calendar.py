from pathlib import Path

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.sites.models import Site
from django.contrib.syndication.views import add_domain
from django.db.models import Count, OuterRef, QuerySet, Subquery
from django.http import HttpRequest
from django.urls import reverse
from django.utils import timezone
from ical.calendar import Calendar
from ical.calendar_stream import IcsCalendarStream
from ical.event import Event
from ical.types import Frequency, Recur

from com.models import News, NewsDate
from core.models import User


def as_absolute_url(url: str, request: HttpRequest | None = None) -> str:
    return add_domain(
        Site.objects.get_current(request=request),
        url,
        secure=request.is_secure() if request is not None else settings.HTTPS,
    )


class IcsCalendar:
    _CACHE_FOLDER: Path = settings.MEDIA_ROOT / "com" / "calendars"
    _INTERNAL_CALENDAR = _CACHE_FOLDER / "internal.ics"

    @classmethod
    def get_internal(cls) -> Path:
        if not cls._INTERNAL_CALENDAR.exists():
            return cls.make_internal()
        return cls._INTERNAL_CALENDAR

    @classmethod
    def make_internal(cls) -> Path:
        # Updated through a post_save signal on News in com.signals
        # Create a file so we can offload the download to the reverse proxy if available
        cls._CACHE_FOLDER.mkdir(parents=True, exist_ok=True)
        with open(cls._INTERNAL_CALENDAR, "wb") as f:
            _ = f.write(
                cls.ics_from_queryset(
                    News.objects.filter(
                        is_published=True,
                        dates__end_date__gte=timezone.now() - relativedelta(months=6),
                    )
                )
            )
        return cls._INTERNAL_CALENDAR

    @classmethod
    def get_unpublished(cls, user: User) -> bytes:
        return cls.ics_from_queryset(
            News.objects.viewable_by(user).filter(
                is_published=False,
                dates__end_date__gte=timezone.now() - relativedelta(months=6),
            )
        )

    @classmethod
    def ics_from_queryset(cls, queryset: QuerySet[News]) -> bytes:
        calendar = Calendar()
        date_subquery = NewsDate.objects.filter(news=OuterRef("pk")).order_by(
            "start_date"
        )
        queryset = queryset.annotate(
            start=Subquery(date_subquery.values("start_date")[:1]),
            end=Subquery(date_subquery.values("end_date")[:1]),
            nb_dates=Count("dates"),
        )
        for news in queryset:
            event = Event(
                summary=news.title,
                description=news.summary,
                dtstart=news.start,
                dtend=news.end,
                url=as_absolute_url(
                    reverse("com:news_detail", kwargs={"news_id": news.id})
                ),
            )
            if news.nb_dates > 1:
                event.rrule = Recur(freq=Frequency.WEEKLY, count=news.nb_dates)
            calendar.events.append(event)

        return IcsCalendarStream.calendar_to_ics(calendar).encode("utf-8")
