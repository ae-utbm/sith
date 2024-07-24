import logging
from time import localtime, strftime
from typing import Any

from django.http import HttpRequest, HttpResponse

from core.utils import get_client_ip


def custom_honeypot_error(
    request: HttpRequest, context: dict[str, Any]
) -> HttpResponse:
    logging.warning(
        f"[{strftime('%c', localtime())}] "
        f"HoneyPot blocked user with ip {get_client_ip(request)}"
    )
    return HttpResponse("Upon reading this, the http client was enlightened.")
