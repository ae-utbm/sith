import os
from urllib.parse import urlparse

from django.conf import settings
from django.http import HttpRequest

from april import views


class AprilFoolMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest):
        if request.user.is_authenticated and request.user.id == os.environ.get(
            "SLI_ID"
        ):
            # Sli deserves a special one :)
            return views.april_fool_sli(request)
        if self._prank_user(request):
            return views.april_fool(request)
        return self.get_response(request)

    @classmethod
    def _prank_user(cls, request):
        if request.user.is_anonymous or not request.user.was_subscribed:
            return False
        # fool users only if the request isn't originated from the sith itself
        referer = request.META.get("HTTP_REFERER", None)
        if referer is not None or urlparse(referer).netloc == settings.SITH_URL:
            return False
        # don't fool a user too often, or his UX will become miserable
        already_pranked = request.COOKIES.get("prankDone")
        return not already_pranked
