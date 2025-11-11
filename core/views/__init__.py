#
# Copyright 2016,2017
# - Skia <skia@libskia.so>
# - Sli <antoine@bartuccio.fr>
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
from django.http import (
    Http404,
    HttpRequest,
    HttpResponseForbidden,
    HttpResponseServerError,
)
from django.shortcuts import render
from django.views.generic.detail import BaseDetailView
from django.views.generic.edit import FormView
from sentry_sdk import last_event_id

from core.views.forms import LoginForm
from core.views.page import PageNotFound


def forbidden(request: HttpRequest, exception):
    context = {"next": request.path, "form": LoginForm()}
    return HttpResponseForbidden(render(request, "core/403.jinja", context=context))


def not_found(request: HttpRequest, exception: Http404):
    if isinstance(exception, PageNotFound):
        template_name = "core/page/not_found.jinja"
    else:
        template_name = "core/404.jinja"
    return render(request, template_name, context={"exception": exception}, status=404)


def internal_servor_error(request):
    request.sentry_last_event_id = last_event_id
    return HttpResponseServerError(render(request, "core/500.jinja"))


class DetailFormView(FormView, BaseDetailView):
    """Class that allow both a detail view and a form view."""

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)


# F403: those star-imports would be hellish to refactor
# E402: putting those import at the top of the file would also be difficult
from .files import *  # noqa: F403 E402
from .group import *  # noqa: F403 E402
from .index import *  # noqa: F403 E402
from .page import *  # noqa: F403 E402
from .user import *  # noqa: F403 E402
