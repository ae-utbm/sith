from typing import TYPE_CHECKING, Callable

from django.db.models import Exists, OuterRef
from django.http import HttpRequest, HttpResponse
from django.utils.functional import SimpleLazyObject, empty

from core.models import User
from counter.models import Permanency

if TYPE_CHECKING:
    from django.contrib.sessions.backends.base import SessionBase


SESSION_BARMEN_KEY = "barmen_ids"


def get_cached_barmen(request: HttpRequest) -> set[User]:
    if not hasattr(request, "_cached_barmen"):
        session: SessionBase = request.session
        barmen_ids = session.get(SESSION_BARMEN_KEY, [])
        if barmen_ids:
            request._cached_barmen = set(
                User.objects.filter(
                    Exists(Permanency.objects.filter(user=OuterRef("pk"), end=None)),
                    id__in=barmen_ids,
                )
            )
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

        response = self.get_response(request)

        if request.barmen._wrapped is not empty and {
            b.id for b in request.barmen
        } != set(request.session.get(SESSION_BARMEN_KEY, [])):
            # update the session data only if `session.barmen`
            # has been accessed and modified.
            request.session[SESSION_BARMEN_KEY] = [b.id for b in request.barmen]
        return response
