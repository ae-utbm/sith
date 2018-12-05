# -*- coding:utf-8 -*
#
# Copyright 2016,2017
# - Skia <skia@libskia.so>
#
# Ce fichier fait partie du site de l'Association des Étudiants de l'UTBM,
# http://ae.utbm.fr.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License a published by the Free Software
# Foundation; either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Sofware Foundation, Inc., 59 Temple
# Place - Suite 330, Boston, MA 02111-1307, USA.
#
#

import importlib
from django.conf import settings
from django.utils.functional import SimpleLazyObject
from django.contrib.auth import get_user
from django.contrib.auth.middleware import (
    AuthenticationMiddleware as DjangoAuthenticationMiddleware,
)

module, klass = settings.AUTH_ANONYMOUS_MODEL.rsplit(".", 1)
AnonymousUser = getattr(importlib.import_module(module), klass)


def get_cached_user(request):
    if not hasattr(request, "_cached_user"):
        user = get_user(request)
        if user.is_anonymous():
            user = AnonymousUser(request)

        request._cached_user = user

    return request._cached_user


class AuthenticationMiddleware(DjangoAuthenticationMiddleware):
    def process_request(self, request):
        assert hasattr(request, "session"), (
            "The Django authentication middleware requires session middleware "
            "to be installed. Edit your MIDDLEWARE_CLASSES setting to insert "
            "'django.contrib.sessions.middleware.SessionMiddleware' before "
            "'account.middleware.AuthenticationMiddleware'."
        )
        request.user = SimpleLazyObject(lambda: get_cached_user(request))
