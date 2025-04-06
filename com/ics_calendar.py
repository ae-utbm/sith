from pathlib import Path
from typing import final

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db.models import F, QuerySet
from django.urls import reverse
from django.utils import timezone
from ical.calendar import Calendar
from ical.calendar_stream import IcsCalendarStream
from ical.event import Event

from com.models import NewsDate
from core.models import User


@final
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
                    NewsDate.objects.filter(
                        news__is_published=True,
                        end_date__gte=timezone.now() - (relativedelta(months=6)),
                    )
                )
            )
        return cls._INTERNAL_CALENDAR

    @classmethod
    def get_unpublished(cls, user: User) -> bytes:
        return cls.ics_from_queryset(
            NewsDate.objects.viewable_by(user).filter(
                news__is_published=False,
                end_date__gte=timezone.now() - (relativedelta(months=6)),
            ),
        )

    @classmethod
    def ics_from_queryset(cls, queryset: QuerySet[NewsDate]) -> bytes:
        calendar = Calendar()
        for news_date in queryset.annotate(news_title=F("news__title")):
            event = Event(
                summary=news_date.news_title,
                start=news_date.start_date,
                end=news_date.end_date,
                url=reverse("com:news_detail", kwargs={"news_id": news_date.news.id}),
            )
            calendar.events.append(event)

        return IcsCalendarStream.calendar_to_ics(calendar).encode("utf-8")
