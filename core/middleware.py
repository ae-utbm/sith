#
# Copyright 2023 © AE UTBM
# ae@utbm.fr / ae.info@utbm.fr
#
# This file is part of the website of the UTBM Student Association (AE UTBM),
# https://ae.utbm.fr.
#
# You can find the source code of the website at https://github.com/ae-utbm/sith
#
# LICENSED UNDER THE GNU GENERAL PUBLIC LICENSE VERSION 3 (GPLv3)
# SEE : https://raw.githubusercontent.com/ae-utbm/sith/master/LICENSE
# OR WITHIN THE LOCAL FILE "LICENSE"
#
#

import importlib
import threading

from django.conf import settings
from django.contrib.auth import get_user
from django.contrib.auth.middleware import (
    AuthenticationMiddleware as DjangoAuthenticationMiddleware,
)
from django.utils.functional import SimpleLazyObject

module, klass = settings.AUTH_ANONYMOUS_MODEL.rsplit(".", 1)
AnonymousUser = getattr(importlib.import_module(module), klass)


def get_cached_user(request):
    if not hasattr(request, "_cached_user"):
        user = get_user(request)
        if user.is_anonymous:
            user = AnonymousUser()

        request._cached_user = user

    return request._cached_user


class AuthenticationMiddleware(DjangoAuthenticationMiddleware):
    def process_request(self, request):
        assert hasattr(request, "session"), (
            "The Django authentication middleware requires session middleware "
            "to be installed. Edit your MIDDLEWARE setting to insert "
            "'django.contrib.sessions.middleware.SessionMiddleware' before "
            "'account.middleware.AuthenticationMiddleware'."
        )
        request.user = SimpleLazyObject(lambda: get_cached_user(request))


_threadlocal = threading.local()


def get_signal_request():
    """Allow to access current request in signals.

    This is a hack that looks into the thread
    Mainly used for log purpose.

    !!!danger
        Do not use if your operation is asynchronous.
    """
    return getattr(_threadlocal, "request", None)


class SignalRequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _threadlocal.request = request
        return self.get_response(request)
