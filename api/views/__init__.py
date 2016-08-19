from rest_framework.response import Response
from rest_framework import viewsets
from django.core.exceptions import PermissionDenied
from rest_framework.decorators import detail_route
from django.db.models.query import QuerySet

from core.views import can_view, can_edit

def check_if(obj, user, test):
    if (isinstance(obj, QuerySet)):
        for o in obj:
            if (test(o, user) is False):
                return False
        return True
    else:
        return test(obj, user)

class RightManagedModelViewSet(viewsets.ReadOnlyModelViewSet):

    @detail_route()
    def id(self, request, pk=None):
        """
            Get by id (api/v1/router/{pk}/id/)
        """
        self.queryset = get_object_or_404(self.queryset.filter(id=pk))
        serializer = self.get_serializer(self.queryset)
        return Response(serializer.data)

    def dispatch(self, request, *arg, **kwargs):
        res = super(RightManagedModelViewSet,
                    self).dispatch(request, *arg, **kwargs)
        obj = self.queryset
        user = self.request.user
        try:
            if (check_if(obj, user, can_view)):
                return res
        except: pass # To prevent bug with Anonymous user
        raise PermissionDenied


from .api import *
from .serializers import *