from rest_framework.response import Response
from rest_framework import viewsets
from django.core.exceptions import PermissionDenied
from rest_framework.decorators import detail_route

from core.views import can_view, can_edit

class RightManagedModelViewSet(viewsets.ModelViewSet):

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
            if (request.method == 'GET' and can_view(obj, user)):
                return res
            elif (request.method == 'PUSH' and can_edit(obj, user)):
                return res
        except: pass # To prevent bug with Anonymous user
        raise PermissionDenied


from .api import *
from .serializers import *