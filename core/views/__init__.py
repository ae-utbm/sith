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

import types

from django.shortcuts import render
from django.http import HttpResponseForbidden, HttpResponseNotFound
from django.core.exceptions import (
    PermissionDenied,
    ObjectDoesNotExist,
    ImproperlyConfigured,
)
from django.views.generic.base import View
from django.db.models import Count

from core.models import Group
from core.views.forms import LoginForm


def forbidden(request):
    try:
        return HttpResponseForbidden(
            render(
                request,
                "core/403.jinja",
                context={
                    "next": request.path,
                    "form": LoginForm(),
                    "popup": request.resolver_match.kwargs["popup"] or "",
                },
            )
        )
    except:
        return HttpResponseForbidden(
            render(
                request,
                "core/403.jinja",
                context={"next": request.path, "form": LoginForm()},
            )
        )


def not_found(request):
    return HttpResponseNotFound(render(request, "core/404.jinja"))


def can_edit_prop(obj, user):
    if obj is None or user.is_owner(obj):
        return True
    return False


def can_edit(obj, user):
    if obj is None or user.can_edit(obj):
        return True
    return can_edit_prop(obj, user)


def can_view(obj, user):
    if obj is None or user.can_view(obj):
        return True
    return can_edit(obj, user)


class CanCreateMixin(View):
    """
    This view is made to protect any child view that would create an object, and thus, that can not be protected by any
    of the following mixin
    """

    def dispatch(self, request, *arg, **kwargs):
        res = super(CanCreateMixin, self).dispatch(request, *arg, **kwargs)
        if not request.user.is_authenticated():
            raise PermissionDenied
        return res

    def form_valid(self, form):
        obj = form.instance
        if can_edit_prop(obj, self.request.user):
            return super(CanCreateMixin, self).form_valid(form)
        raise PermissionDenied


class CanEditPropMixin(View):
    """
    This view is made to protect any child view that would be showing some properties of an object that are restricted
    to only the owner group of the given object.
    In other word, you can make a view with this view as parent, and it would be retricted to the users that are in the
    object's owner_group
    """

    def dispatch(self, request, *arg, **kwargs):
        try:
            self.object = self.get_object()
            if can_edit_prop(self.object, request.user):
                return super(CanEditPropMixin, self).dispatch(request, *arg, **kwargs)
            return forbidden(request)
        except:
            pass
        # If we get here, it's a ListView
        l_id = [o.id for o in self.get_queryset() if can_edit_prop(o, request.user)]
        if not l_id and self.get_queryset().count() != 0:
            raise PermissionDenied
        self._get_queryset = self.get_queryset

        def get_qs(self2):
            return self2._get_queryset().filter(id__in=l_id)

        self.get_queryset = types.MethodType(get_qs, self)
        return super(CanEditPropMixin, self).dispatch(request, *arg, **kwargs)


class CanEditMixin(View):
    """
    This view makes exactly the same thing as its direct parent, but checks the group on the edit_groups field of the
    object
    """

    def dispatch(self, request, *arg, **kwargs):
        try:
            self.object = self.get_object()
            if can_edit(self.object, request.user):
                return super(CanEditMixin, self).dispatch(request, *arg, **kwargs)
            return forbidden(request)
        except:
            pass
        # If we get here, it's a ListView
        l_id = [o.id for o in self.get_queryset() if can_edit(o, request.user)]
        if not l_id and self.get_queryset().count() != 0:
            raise PermissionDenied
        self._get_queryset = self.get_queryset

        def get_qs(self2):
            return self2._get_queryset().filter(id__in=l_id)

        self.get_queryset = types.MethodType(get_qs, self)
        return super(CanEditMixin, self).dispatch(request, *arg, **kwargs)


class CanViewMixin(View):
    """
    This view still makes exactly the same thing as its direct parent, but checks the group on the view_groups field of
    the object
    """

    def dispatch(self, request, *arg, **kwargs):
        try:
            self.object = self.get_object()
            if can_view(self.object, request.user):
                return super(CanViewMixin, self).dispatch(request, *arg, **kwargs)
            return forbidden(request)
        except:
            pass
        # If we get here, it's a ListView
        l_id = [o.id for o in self.get_queryset() if can_view(o, request.user)]
        if not l_id and self.get_queryset().count() != 0:
            raise PermissionDenied
        self._get_queryset = self.get_queryset

        def get_qs(self2):
            return self2._get_queryset().filter(id__in=l_id)

        self.get_queryset = types.MethodType(get_qs, self)
        return super(CanViewMixin, self).dispatch(request, *arg, **kwargs)


class FormerSubscriberMixin(View):
    """
    This view check if the user was at least an old subscriber
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.was_subscribed:
            raise PermissionDenied
        return super(FormerSubscriberMixin, self).dispatch(request, *args, **kwargs)


class TabedViewMixin(View):
    """
    This view provide the basic functions for displaying tabs in the template
    """

    def get_tabs_title(self):
        try:
            return self.tabs_title
        except:
            raise ImproperlyConfigured("tabs_title is required")

    def get_current_tab(self):
        try:
            return self.current_tab
        except:
            raise ImproperlyConfigured("current_tab is required")

    def get_list_of_tabs(self):
        try:
            return self.list_of_tabs
        except:
            raise ImproperlyConfigured("list_of_tabs is required")

    def get_context_data(self, **kwargs):
        kwargs = super(TabedViewMixin, self).get_context_data(**kwargs)
        kwargs["tabs_title"] = self.get_tabs_title()
        kwargs["current_tab"] = self.get_current_tab()
        kwargs["list_of_tabs"] = self.get_list_of_tabs()
        return kwargs


class QuickNotifMixin:
    quick_notif_list = []

    def dispatch(self, request, *arg, **kwargs):
        self.quick_notif_list = (
            []
        )  # In some cases, the class can stay instanciated, so we need to reset the list
        return super(QuickNotifMixin, self).dispatch(request, *arg, **kwargs)

    def get_success_url(self):
        ret = super(QuickNotifMixin, self).get_success_url()
        try:
            if "?" in ret:
                ret += "&" + self.quick_notif_url_arg
            else:
                ret += "?" + self.quick_notif_url_arg
        except:
            pass
        return ret

    def get_context_data(self, **kwargs):
        """Add quick notifications to context"""
        kwargs = super(QuickNotifMixin, self).get_context_data(**kwargs)
        kwargs["quick_notifs"] = []
        for n in self.quick_notif_list:
            kwargs["quick_notifs"].append(settings.SITH_QUICK_NOTIF[n])
        for k, v in settings.SITH_QUICK_NOTIF.items():
            for gk in self.request.GET.keys():
                if k == gk:
                    kwargs["quick_notifs"].append(v)
        return kwargs


from .user import *
from .page import *
from .files import *
from .site import *
from .group import *
