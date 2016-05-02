
from django.shortcuts import render
from django.http import HttpResponseForbidden, HttpResponseNotFound
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.views.generic.base import View

from core.models import Group

def forbidden(request):
    return HttpResponseForbidden(render(request, "core/403.jinja"))

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

class CanEditPropMixin(View):
    """
    This view is made to protect any child view that would be showing some properties of an object that are restricted
    to only the owner group of the given object.
    In other word, you can make a view with this view as parent, and it would be retricted to the users that are in the
    object's owner_group
    """
    def dispatch(self, request, *arg, **kwargs):
        res = super(CanEditPropMixin, self).dispatch(request, *arg, **kwargs)
        if hasattr(self, 'object'):
            obj = self.object
        elif hasattr(self, 'object_list'):
            obj = self.object_list[0] if self.object_list else None
        if can_edit_prop(obj, self.request.user):
            return res
        try: # Always unlock when 403
            self.object.unset_lock()
        except: pass
        raise PermissionDenied

class CanEditMixin(View):
    """
    This view makes exactly the same this as its direct parent, but checks the group on the edit_groups field of the
    object
    """
    def dispatch(self, request, *arg, **kwargs):
        res = super(CanEditMixin, self).dispatch(request, *arg, **kwargs)
        if hasattr(self, 'object'):
            obj = self.object
        elif hasattr(self, 'object_list'):
            obj = self.object_list[0] if self.object_list else None
        if can_edit(obj, self.request.user):
            return res
        try: # Always unlock when 403
            self.object.unset_lock()
        except: pass
        raise PermissionDenied

class CanViewMixin(View):
    """
    This view still makes exactly the same this as its direct parent, but checks the group on the view_groups field of
    the object
    """
    def dispatch(self, request, *arg, **kwargs):
        res = super(CanViewMixin, self).dispatch(request, *arg, **kwargs)
        if hasattr(self, 'object'):
            obj = self.object
        elif hasattr(self, 'object_list'):
            obj = self.object_list[0] if self.object_list else None
        if can_view(obj, self.request.user):
            return res
        try: # Always unlock when 403
            self.object.unset_lock()
        except: pass
        raise PermissionDenied

from .user import *
from .page import *
from .site import *
from .group import *
from .api import *

