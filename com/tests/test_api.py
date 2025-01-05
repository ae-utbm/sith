from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable
from unittest.mock import MagicMock, patch

import pytest
from django.conf import settings
from django.http import HttpResponse
from django.test.client import Client
from django.urls import reverse
from django.utils import timezone

from com.calendar import IcsCalendar


@dataclass
class MockResponse:
    status: int
    value: str

    @property
    def data(self):
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
        with patch("urllib3.request", mock):
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

    @pytest.mark.parametrize("error_code", [403, 404, 500])
    def test_fetch_error(
        self, client: Client, mock_request: MagicMock, error_code: int
    ):
        mock_request.return_value = MockResponse(error_code, "not allowed")
        assert client.get(reverse("api:calendar_external")).status_code == 404

    def test_fetch_success(self, client: Client, mock_request: MagicMock):
        external_response = MockResponse(200, "Definitely an ICS")
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
