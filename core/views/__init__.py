
from django.shortcuts import render
from django.http import HttpResponseForbidden
from django.core.exceptions import PermissionDenied
from django.views.generic.base import View

from core.models import Group

def forbidden(request):
    return render(request, "core/403.html")

def not_found(request):
    return render(request, "core/404.html")


# TODO: see models.py's TODO!
class CanEditPropMixin(View):
    """
    This view is made to protect any child view that would be showing some properties of an object that are restricted
    to only the owner group of the given object.
    In other word, you can make a view with this view as parent, and it would be retricted to the users that are in the
    object's owner_group
    """
    def dispatch(self, request, *arg, **kwargs):
        res = super(CanEditPropMixin, self).dispatch(request, *arg, **kwargs)
        obj = self.object
        user = self.request.user
        if obj is None:
            return res
        # TODO: add permission scale validation, to allow some groups other than superuser to manipulate
        # all objects of a class if they are in the right group
        if user.is_superuser or user.groups.filter(name=obj.owner_group.name).exists():
            return res
        raise PermissionDenied
        return HttpResponseForbidden("403, Forbidden")

class CanEditMixin(CanEditPropMixin):
    """
    This view makes exactly the same this as its direct parent, but checks the group on the edit_group field of the
    object
    """
    def dispatch(self, request, *arg, **kwargs):
        # TODO: WIP: fix permissions with exceptions!
        try:
            res = super(CanEditMixin, self).dispatch(request, *arg, **kwargs)
        except PermissionDenied:
            pass
        except:
            return res
        obj = self.object
        user = self.request.user
        if obj is None:
            return res
        for g in obj.edit_group.all():
            if user.groups.filter(name=g.name).exists():
                return super(CanEditPropMixin, self).dispatch(request, *arg, **kwargs)
        if isinstance(obj, User) and obj == user:
            return super(CanEditPropMixin, self).dispatch(request, *arg, **kwargs)
        raise PermissionDenied
        return HttpResponseForbidden("403, Forbidden")

class CanViewMixin(CanEditMixin):
    """
    This view still makes exactly the same this as its direct parent, but checks the group on the view_group field of
    the object
    """
    def dispatch(self, request, *arg, **kwargs):
        try:
            res = super(CanViewMixin, self).dispatch(request, *arg, **kwargs)
        except PermissionDenied:
            pass
        except:
            return res
        obj = self.object
        user = self.request.user
        if obj is None:
            return res
        for g in obj.view_group.all():
            if user.groups.filter(name=g.name).exists():
                return super(CanEditPropMixin, self).dispatch(request, *arg, **kwargs)
        raise PermissionDenied
        return HttpResponseForbidden("403, Forbidden")

from .user import *
from .page import *
from .site import *
from .group import *

