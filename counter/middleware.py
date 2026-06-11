from typing import TYPE_CHECKING, Callable

from django.http import HttpRequest, HttpResponse
from django.utils.functional import SimpleLazyObject

from core.models import User
from counter.models import Permanency

if TYPE_CHECKING:
    from django.contrib.sessions.backends.base import SessionBase


SESSION_PERMANENCES_KEY = "permanence_ids"


def get_cached_barmen(request: HttpRequest) -> set[User]:
    if not hasattr(request, "_cached_barmen"):
        session: SessionBase = request.session

        if session_ids := session.get(SESSION_PERMANENCES_KEY, None):
            # Get ongoing permanences which id is in session.
            # Note : we store permanence ids rather than user id to be sure
            # not to wrongfully mark someone as logged here,
            # even if it logged out then logged in elsewhere.
            permanences = (
                Permanency.objects.filter(end=None, id__in=session_ids)
                .order_by("id")
                .select_related("user")
            )

            # if the list of permanences occurring on this device has changed
            # since the last page load, change the ids stored in session
            real_ids = [p.id for p in permanences]
            if real_ids != session_ids:
                session[SESSION_PERMANENCES_KEY] = real_ids

            request._cached_barmen = {p.user for p in permanences}
        else:
            request._cached_barmen = set()

    return request._cached_barmen


class BarmenMiddleware:
    """Inject barmen logged in the current session.

    In a similar fashion as `request.user`, `request.barmen` contains
    users that are barmen in the current session, and ONLY them ;
    if a user is logged as a barman on another session,
    it will not be in `request.barmen`.

    Notes:
        In case of ended permanence, users will be automatically
        removed from `request.barmen`.
        However, in case of newly started permanence, this middleware
        cannot add new barmen in the session data, so that operation
        must be explicitly done in the barman login view.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        request.barmen = SimpleLazyObject(lambda: get_cached_barmen(request))

        return self.get_response(request)
