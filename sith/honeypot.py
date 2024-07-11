import logging
from typing import Any

from django.http import HttpResponse
from django.test.client import WSGIRequest


def custom_honeypot_error(
    request: WSGIRequest, context: dict[str, Any]
) -> HttpResponse:
    logging.warning(f"HoneyPot blocked user with ip {request.META.get('REMOTE_ADDR')}")
    return HttpResponse("Upon reading this, the http client was enlightened.")
