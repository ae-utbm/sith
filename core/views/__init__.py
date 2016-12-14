import types

from django.shortcuts import render
from django.http import HttpResponseForbidden, HttpResponseNotFound
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist, ImproperlyConfigured
from django.views.generic.base import View

from core.models import Group
from core.views.forms import LoginForm

def forbidden(request):
    try:
        return HttpResponseForbidden(render(request, "core/403.jinja", context={'next': request.path, 'form':
            LoginForm(), 'popup': request.resolver_match.kwargs['popup'] or ""}))
    except:
        return HttpResponseForbidden(render(request, "core/403.jinja", context={'next': request.path, 'form': LoginForm()}))

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
        except: pass
        # If we get here, it's a ListView
        l_id = [o.id for o in self.get_queryset() if can_edit_prop(o, request.user)]
        if not l_id:
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
        except: pass
        # If we get here, it's a ListView
        l_id = [o.id for o in self.get_queryset() if can_edit(o, request.user)]
        if not l_id:
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
        except: pass
        # If we get here, it's a ListView
        l_id = [o.id for o in self.get_queryset() if can_view(o, request.user)]
        if not l_id:
            raise PermissionDenied
        self._get_queryset = self.get_queryset
        def get_qs(self2):
            return self2._get_queryset().filter(id__in=l_id)
        self.get_queryset = types.MethodType(get_qs, self)
        return super(CanViewMixin, self).dispatch(request, *arg, **kwargs)

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
        kwargs['tabs_title'] = self.get_tabs_title()
        kwargs['current_tab'] = self.get_current_tab()
        kwargs['list_of_tabs'] = self.get_list_of_tabs()
        return kwargs

from .user import *
from .page import *
from .files import *
from .site import *
from .group import *


