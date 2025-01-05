from dataclasses import dataclass
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from django.conf import settings
from django.test.client import Client
from django.urls import reverse

from com.calendar import IcsCalendar


@dataclass
class MockResponse:
    status: int
    value: str

    @property
    def data(self):
        return self.value.encode("utf8")


@pytest.mark.django_db
class TestExternalCalendar:
    @pytest.fixture
    def mock_request(self):
        request = MagicMock()
        with patch("urllib3.request", request):
            yield request

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
        redirect = Path(response.headers.get("X-Accel-Redirect", ""))
        assert redirect.is_relative_to(Path("/") / settings.MEDIA_ROOT.stem)
        out_file = settings.MEDIA_ROOT / redirect.relative_to(
            Path("/") / settings.MEDIA_ROOT.stem
        )
        assert out_file.exists()
        with open(out_file, "r") as f:
            assert f.read() == external_response.value
