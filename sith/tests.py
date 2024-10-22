from contextlib import nullcontext as does_not_raise

import pytest
from _pytest.python_api import RaisesContext
from django.test import Client
from django.test.utils import override_settings
from django.urls import reverse


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("sentry_dsn", "sentry_env", "expected_error", "expected_return_code"),
    [
        # Working case
        ("something", "development", pytest.raises(ZeroDivisionError), None),
        # View is disabled when DSN isn't defined or environment isn't development
        ("something", "production", does_not_raise(), 404),
        ("", "development", does_not_raise(), 404),
        ("", "production", does_not_raise(), 404),
    ],
)
def test_sentry_debug_endpoint(
    client: Client,
    sentry_dsn: str,
    sentry_env: str,
    expected_error: RaisesContext[ZeroDivisionError] | does_not_raise[None],
    expected_return_code: int | None,
):
    with expected_error, override_settings(
        SENTRY_DSN=sentry_dsn, SENTRY_ENV=sentry_env
    ):
        assert client.get(reverse("sentry-debug")).status_code == expected_return_code
