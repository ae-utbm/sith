
from django.shortcuts import render
from django.http import HttpResponseForbidden
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.views.generic.base import View

from core.models import Group

def forbidden(request):
    return render(request, "core/403.jinja")

def not_found(request):
    return render(request, "core/404.jinja")


class CanEditPropMixin(View):
    """
    This view is made to protect any child view that would be showing some properties of an object that are restricted
    to only the owner group of the given object.
    In other word, you can make a view with this view as parent, and it would be retricted to the users that are in the
    object's owner_group
    """
    def dispatch(self, request, *arg, **kwargs):
        res = super(CanEditPropMixin, self).dispatch(request, *arg, **kwargs)
        if ((hasattr(self, 'object') and (self.object is None or self.request.user.is_owner(self.object))) or
            (hasattr(self, 'object_list') and (self.object_list is None or self.object_list is [] or self.request.user.is_owner(self.object_list[0])))):
            return res
        try: # Always unlock when 403
            self.object.unset_lock()
        except: pass
        raise PermissionDenied

class CanEditMixin(View):
    """
    This view makes exactly the same this as its direct parent, but checks the group on the edit_group field of the
    object
    """
    def dispatch(self, request, *arg, **kwargs):
        # TODO: WIP: fix permissions with exceptions!
        res = super(CanEditMixin, self).dispatch(request, *arg, **kwargs)
        if ((hasattr(self, 'object') and (self.object is None or self.request.user.can_edit(self.object))) or
            (hasattr(self, 'object_list') and (self.object_list is None or self.object_list is [] or self.request.user.can_edit(self.object_list[0])))):
            return res
        try: # Always unlock when 403
            self.object.unset_lock()
        except: pass
        print("CanEditMixin 403")
        raise PermissionDenied

class CanViewMixin(View):
    """
    This view still makes exactly the same this as its direct parent, but checks the group on the view_group field of
    the object
    """
    def dispatch(self, request, *arg, **kwargs):
        res = super(CanViewMixin, self).dispatch(request, *arg, **kwargs)
        if ((hasattr(self, 'object') and (self.object is None or self.request.user.can_view(self.object))) or
            (hasattr(self, 'object_list') and (self.object_list is None or self.object_list is [] or self.request.user.can_view(self.object_list[0])))):
            return res
        try: # Always unlock when 403
            self.object.unset_lock()
        except: pass
        print("CanViewMixin 403")
        raise PermissionDenied

from .user import *
from .page import *
from .site import *
from .group import *
from .api import *

