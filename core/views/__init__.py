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

import types
from typing import Any

from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import (
    ImproperlyConfigured,
    PermissionDenied,
)
from django.http import (
    HttpResponseForbidden,
    HttpResponseNotFound,
    HttpResponseServerError,
)
from django.utils.functional import cached_property
from django.views.generic.base import View
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import FormView
from sentry_sdk import last_event_id

from core.models import User
from core.views.forms import LoginForm


def forbidden(request, exception):
    context = {"next": request.path, "form": LoginForm()}
    if popup := request.resolver_match.kwargs.get("popup"):
        context["popup"] = popup
    return HttpResponseForbidden(render(request, "core/403.jinja", context=context))


def not_found(request, exception):
    return HttpResponseNotFound(
        render(request, "core/404.jinja", context={"exception": exception})
    )


def internal_servor_error(request):
    request.sentry_last_event_id = last_event_id
    return HttpResponseServerError(render(request, "core/500.jinja"))


def can_edit_prop(obj: Any, user: User) -> bool:
    """Can the user edit the properties of the object.

    Args:
        obj: Object to test for permission
        user: core.models.User to test permissions against

    Returns:
        True if user is authorized to edit object properties else False

    Examples:
        ```python
        if not can_edit_prop(self.object ,request.user):
            raise PermissionDenied
        ```
    """
    if obj is None or user.is_owner(obj):
        return True
    return False


def can_edit(obj: Any, user: User):
    """Can the user edit the object.

    Args:
        obj: Object to test for permission
        user: core.models.User to test permissions against

    Returns:
        True if user is authorized to edit object else False

    Examples:
        ```python
        if not can_edit(self.object, request.user):
            raise PermissionDenied
        ```
    """
    if obj is None or user.can_edit(obj):
        return True
    return can_edit_prop(obj, user)


def can_view(obj: Any, user: User):
    """Can the user see the object.

    Args:
        obj: Object to test for permission
        user: core.models.User to test permissions against

    Returns:
        True if user is authorized to see object else False

    Examples:
        ```python
        if not can_view(self.object ,request.user):
            raise PermissionDenied
        ```
    """
    if obj is None or user.can_view(obj):
        return True
    return can_edit(obj, user)


class GenericContentPermissionMixinBuilder(View):
    """Used to build permission mixins.

    This view protect any child view that would be showing an object that is restricted based
      on two properties.

    Attributes:
        raised_error: permission to be raised
    """

    raised_error = PermissionDenied

    @staticmethod
    def permission_function(obj: Any, user: User) -> bool:
        """Function to test permission with."""
        return False

    @classmethod
    def get_permission_function(cls, obj, user):
        return cls.permission_function(obj, user)

    def dispatch(self, request, *arg, **kwargs):
        if hasattr(self, "get_object") and callable(self.get_object):
            self.object = self.get_object()
            if not self.get_permission_function(self.object, request.user):
                raise self.raised_error
            return super().dispatch(request, *arg, **kwargs)

        # If we get here, it's a ListView

        queryset = self.get_queryset()
        l_id = [o.id for o in queryset if self.get_permission_function(o, request.user)]
        if not l_id and queryset.count() != 0:
            raise self.raised_error
        self._get_queryset = self.get_queryset

        def get_qs(self2):
            return self2._get_queryset().filter(id__in=l_id)

        self.get_queryset = types.MethodType(get_qs, self)
        return super().dispatch(request, *arg, **kwargs)


class CanCreateMixin(View):
    """Protect any child view that would create an object.

    Raises:
        PermissionDenied:
            If the user has not the necessary permission
            to create the object of the view.
    """

    def dispatch(self, request, *arg, **kwargs):
        res = super().dispatch(request, *arg, **kwargs)
        if not request.user.is_authenticated:
            raise PermissionDenied
        return res

    def form_valid(self, form):
        obj = form.instance
        if can_edit_prop(obj, self.request.user):
            return super().form_valid(form)
        raise PermissionDenied


class CanEditPropMixin(GenericContentPermissionMixinBuilder):
    """Ensure the user has owner permissions on the child view object.

    In other word, you can make a view with this view as parent,
    and it will be retricted to the users that are in the
    object's owner_group or that pass the `obj.can_be_viewed_by` test.

    Raises:
        PermissionDenied: If the user cannot see the object
    """

    permission_function = can_edit_prop


class CanEditMixin(GenericContentPermissionMixinBuilder):
    """Ensure the user has permission to edit this view's object.

    Raises:
        PermissionDenied: if the user cannot edit this view's object.
    """

    permission_function = can_edit


class CanViewMixin(GenericContentPermissionMixinBuilder):
    """Ensure the user has permission to view this view's object.

    Raises:
        PermissionDenied: if the user cannot edit this view's object.
    """

    permission_function = can_view


class UserIsRootMixin(GenericContentPermissionMixinBuilder):
    """Allow only root admins.

    Raises:
        PermissionDenied: if the user isn't root
    """

    permission_function = lambda obj, user: user.is_root


class FormerSubscriberMixin(AccessMixin):
    """Check if the user was at least an old subscriber.

    Raises:
        PermissionDenied: if the user never subscribed.
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.was_subscribed:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class SubscriberMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_subscribed:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class TabedViewMixin(View):
    """Basic functions for displaying tabs in the template."""

    def get_tabs_title(self):
        if hasattr(self, "tabs_title"):
            return self.tabs_title
        raise ImproperlyConfigured("tabs_title is required")

    def get_current_tab(self):
        if hasattr(self, "current_tab"):
            return self.current_tab
        raise ImproperlyConfigured("current_tab is required")

    def get_list_of_tabs(self):
        if hasattr(self, "list_of_tabs"):
            return self.list_of_tabs
        raise ImproperlyConfigured("list_of_tabs is required")

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs["tabs_title"] = self.get_tabs_title()
        kwargs["current_tab"] = self.get_current_tab()
        kwargs["list_of_tabs"] = self.get_list_of_tabs()
        return kwargs


class QuickNotifMixin:
    quick_notif_list = []

    def dispatch(self, request, *arg, **kwargs):
        # In some cases, the class can stay instanciated, so we need to reset the list
        self.quick_notif_list = []
        return super().dispatch(request, *arg, **kwargs)

    def get_success_url(self):
        ret = super().get_success_url()
        if hasattr(self, "quick_notif_url_arg"):
            if "?" in ret:
                ret += "&" + self.quick_notif_url_arg
            else:
                ret += "?" + self.quick_notif_url_arg
        return ret

    def get_context_data(self, **kwargs):
        """Add quick notifications to context."""
        kwargs = super().get_context_data(**kwargs)
        kwargs["quick_notifs"] = []
        for n in self.quick_notif_list:
            kwargs["quick_notifs"].append(settings.SITH_QUICK_NOTIF[n])
        for k, v in settings.SITH_QUICK_NOTIF.items():
            for gk in self.request.GET.keys():
                if k == gk:
                    kwargs["quick_notifs"].append(v)
        return kwargs


class DetailFormView(SingleObjectMixin, FormView):
    """Class that allow both a detail view and a form view."""

    def get_object(self):
        """Get current group from id in url."""
        return self.cached_object

    @cached_property
    def cached_object(self):
        """Optimisation on group retrieval."""
        return super().get_object()


from .files import *
from .group import *
from .page import *
from .site import *
from .user import *
