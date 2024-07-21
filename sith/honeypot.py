import logging
from time import localtime, strftime
from typing import Any

from django.http import HttpRequest, HttpResponse


def custom_honeypot_error(
    request: HttpRequest, context: dict[str, Any]
) -> HttpResponse:
    logging.warning(
        f"[{strftime('%c', localtime())}] "
        f"HoneyPot blocked user with ip {request.META.get('X-Forwarded-For')}"
    )
    return HttpResponse("Upon reading this, the http client was enlightened.")
