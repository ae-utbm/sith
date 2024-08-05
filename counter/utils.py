from urllib.parse import urlparse

from django.http import HttpRequest
from django.urls import resolve

from counter.models import Counter


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
    - The current session has a counter token associated with it.
    - A counter with this token exists.
    """
    referer = urlparse(request.META["HTTP_REFERER"]).path
    path_ok = (
        request.resolver_match.app_name == "counter"
        or resolve(referer).app_name == "counter"
    )
    return (
        path_ok
        and "counter_token" in request.session
        and request.session["counter_token"]
        and Counter.objects.filter(token=request.session["counter_token"]).exists()
    )
