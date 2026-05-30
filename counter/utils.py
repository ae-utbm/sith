from urllib.parse import urlparse

from django.http import HttpRequest
from django.urls import resolve


def is_logged_in_counter(request: HttpRequest) -> bool:
    """Check if the request is sent from a device logged to a counter.

    The request must also be sent within the frame of a counter's activity.
    Trying to use this function to manage access to non-sas
    related resources probably won't work.

    A request is considered as coming from a logged counter if :

    - Its referer comes from the counter app
      (eg. fetching user pictures from the click UI)
      or the request path belongs to the counter app
      (eg. the barman went back to the main by missclick and go back
      to the counter)
    - There are barmen logged in the current session
    """
    referer_ok = (
        "HTTP_REFERER" in request.META
        and resolve(urlparse(request.META["HTTP_REFERER"]).path).app_name == "counter"
    )
    if not referer_ok and request.resolver_match.app_name != "counter":
        return False

    return bool(request.barmen)
