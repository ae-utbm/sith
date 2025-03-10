from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable
from unittest.mock import MagicMock, patch
from urllib.parse import quote

import pytest
from django.conf import settings
from django.contrib.auth.models import Permission
from django.http import HttpResponse
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.timezone import now
from model_bakery import baker, seq
from pytest_django.asserts import assertNumQueries

from com.ics_calendar import IcsCalendar
from com.models import News, NewsDate
from core.markdown import markdown
from core.models import User


@dataclass
class MockResponse:
    ok: bool
    value: str

    @property
    def content(self):
        return self.value.encode("utf8")


def accel_redirect_to_file(response: HttpResponse) -> Path | None:
    redirect = Path(response.headers.get("X-Accel-Redirect", ""))
    if not redirect.is_relative_to(Path("/") / settings.MEDIA_ROOT.stem):
        return None
    return settings.MEDIA_ROOT / redirect.relative_to(
        Path("/") / settings.MEDIA_ROOT.stem
    )


@pytest.mark.django_db
class TestExternalCalendar:
    @pytest.fixture
    def mock_request(self):
        mock = MagicMock()
        with patch("requests.get", mock):
            yield mock

    @pytest.fixture
    def mock_current_time(self):
        mock = MagicMock()
        original = timezone.now
        with patch("django.utils.timezone.now", mock):
            yield mock, original

    @pytest.fixture(autouse=True)
    def clear_cache(self):
        IcsCalendar._EXTERNAL_CALENDAR.unlink(missing_ok=True)

    def test_fetch_error(self, client: Client, mock_request: MagicMock):
        mock_request.return_value = MockResponse(ok=False, value="not allowed")
        assert client.get(reverse("api:calendar_external")).status_code == 404

    def test_fetch_success(self, client: Client, mock_request: MagicMock):
        external_response = MockResponse(ok=True, value="Definitely an ICS")
        mock_request.return_value = external_response
        response = client.get(reverse("api:calendar_external"))
        assert response.status_code == 200
        out_file = accel_redirect_to_file(response)
        assert out_file is not None
        assert out_file.exists()
        with open(out_file, "r") as f:
            assert f.read() == external_response.value

    def test_fetch_caching(
        self,
        client: Client,
        mock_request: MagicMock,
        mock_current_time: tuple[MagicMock, Callable[[], datetime]],
    ):
        fake_current_time, original_timezone = mock_current_time
        start_time = original_timezone()

        fake_current_time.return_value = start_time
        external_response = MockResponse(200, "Definitely an ICS")
        mock_request.return_value = external_response

        with open(
            accel_redirect_to_file(client.get(reverse("api:calendar_external"))), "r"
        ) as f:
            assert f.read() == external_response.value

        mock_request.return_value = MockResponse(200, "This should be ignored")
        with open(
            accel_redirect_to_file(client.get(reverse("api:calendar_external"))), "r"
        ) as f:
            assert f.read() == external_response.value

        mock_request.assert_called_once()

        fake_current_time.return_value = start_time + timedelta(hours=1, seconds=1)
        external_response = MockResponse(200, "This won't be ignored")
        mock_request.return_value = external_response

        with open(
            accel_redirect_to_file(client.get(reverse("api:calendar_external"))), "r"
        ) as f:
            assert f.read() == external_response.value

        assert mock_request.call_count == 2


@pytest.mark.django_db
class TestInternalCalendar:
    @pytest.fixture(autouse=True)
    def clear_cache(self):
        IcsCalendar._INTERNAL_CALENDAR.unlink(missing_ok=True)

    def test_fetch_success(self, client: Client):
        response = client.get(reverse("api:calendar_internal"))
        assert response.status_code == 200
        out_file = accel_redirect_to_file(response)
        assert out_file is not None
        assert out_file.exists()


@pytest.mark.django_db
class TestModerateNews:
    @pytest.mark.parametrize("news_is_published", [True, False])
    def test_moderation_ok(self, client: Client, news_is_published: bool):  # noqa FBT
        user = baker.make(
            User, user_permissions=[Permission.objects.get(codename="moderate_news")]
        )
        # The API call should work even if the news is initially moderated.
        # In the latter case, the result should be a noop, rather than an error.
        news = baker.make(News, is_published=news_is_published)
        initial_moderator = news.moderator
        client.force_login(user)
        response = client.patch(
            reverse("api:moderate_news", kwargs={"news_id": news.id})
        )
        # if it wasn't moderated, it should now be moderated and the moderator should
        # be the user that made the request.
        # If it was already moderated, it should be a no-op, but not an error
        assert response.status_code == 200
        news.refresh_from_db()
        assert news.is_published
        if not news_is_published:
            assert news.moderator == user
        else:
            assert news.moderator == initial_moderator

    def test_moderation_forbidden(self, client: Client):
        user = baker.make(User)
        news = baker.make(News, is_published=False)
        client.force_login(user)
        response = client.patch(
            reverse("api:moderate_news", kwargs={"news_id": news.id})
        )
        assert response.status_code == 403
        news.refresh_from_db()
        assert not news.is_published


@pytest.mark.django_db
class TestDeleteNews:
    def test_delete_news_ok(self, client: Client):
        user = baker.make(
            User, user_permissions=[Permission.objects.get(codename="delete_news")]
        )
        news = baker.make(News)
        client.force_login(user)
        response = client.delete(
            reverse("api:delete_news", kwargs={"news_id": news.id})
        )
        assert response.status_code == 200
        assert not News.objects.filter(id=news.id).exists()

    def test_delete_news_forbidden(self, client: Client):
        user = baker.make(User)
        news = baker.make(News)
        client.force_login(user)
        response = client.delete(
            reverse("api:delete_news", kwargs={"news_id": news.id})
        )
        assert response.status_code == 403
        assert News.objects.filter(id=news.id).exists()


class TestFetchNewsDates(TestCase):
    @classmethod
    def setUpTestData(cls):
        News.objects.all().delete()
        cls.dates = baker.make(
            NewsDate,
            _quantity=5,
            _bulk_create=True,
            start_date=seq(value=now(), increment_by=timedelta(days=1)),
            end_date=seq(
                value=now() + timedelta(hours=2), increment_by=timedelta(days=1)
            ),
            news=iter(
                baker.make(News, is_published=True, _quantity=5, _bulk_create=True)
            ),
        )
        cls.dates.append(
            baker.make(
                NewsDate,
                start_date=now() + timedelta(days=2, hours=1),
                end_date=now() + timedelta(days=2, hours=5),
                news=baker.make(News, is_published=True),
            )
        )
        cls.dates.sort(key=lambda d: d.start_date)

    def test_num_queries(self):
        with assertNumQueries(2):
            self.client.get(reverse("api:fetch_news_dates"))

    def test_html_format(self):
        """Test that when the summary is asked in html, the summary is in html."""
        summary_1 = "# First event\nThere is something happening.\n"
        self.dates[0].news.summary = summary_1
        self.dates[0].news.save()
        summary_2 = (
            "# Second event\n"
            "There is something happening **for real**.\n"
            "Everything is [here](https://youtu.be/dQw4w9WgXcQ)\n"
        )
        self.dates[1].news.summary = summary_2
        self.dates[1].news.save()
        response = self.client.get(
            reverse("api:fetch_news_dates") + "?page_size=2&text_format=html"
        )
        assert response.status_code == 200
        dates = response.json()["results"]
        assert dates[0]["news"]["summary"] == markdown(summary_1)
        assert dates[1]["news"]["summary"] == markdown(summary_2)

    def test_fetch(self):
        after = quote((now() + timedelta(days=1)).isoformat())
        response = self.client.get(
            reverse("api:fetch_news_dates") + f"?page_size=3&after={after}"
        )
        assert response.status_code == 200
        dates = response.json()["results"]
        assert [d["id"] for d in dates] == [d.id for d in self.dates[1:4]]
