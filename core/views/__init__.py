
from django.http import HttpResponseForbidden
from django.core.exceptions import PermissionDenied
from django.views.generic.base import View

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
        if user.is_superuser or user.groups.filter(name=obj.owner_group.name).exists():
            return res
        return HttpResponseForbidden("403, Forbidden")

class CanEditMixin(CanEditPropMixin):
    """
    This view makes exactly the same this as its direct parent, but checks the group on the edit_group field of the
    object
    """
    def dispatch(self, request, *arg, **kwargs):
        res = super(CanEditMixin, self).dispatch(request, *arg, **kwargs)
        if res.status_code != 403:
            return res
        obj = self.object
        user = self.request.user
        if obj is None:
            return res
        for g in obj.edit_group.all():
            if user.groups.filter(name=g.name).exists():
                return super(CanEditPropMixin, self).dispatch(request, *arg, **kwargs)
        return HttpResponseForbidden("403, Forbidden")

class CanViewMixin(CanEditMixin):
    """
    This view still makes exactly the same this as its direct parent, but checks the group on the view_group field of
    the object
    """
    def dispatch(self, request, *arg, **kwargs):
        res = super(CanViewMixin, self).dispatch(request, *arg, **kwargs)
        if res.status_code != 403:
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

