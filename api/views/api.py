from . import serializers
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import viewsets
from rest_framework.decorators import detail_route
from rest_framework.decorators import list_route

from django.shortcuts import get_object_or_404
from core.templatetags.renderer import markdown
from counter.models import Counter


@api_view(['GET'])
def RenderMarkdown(request):
    """
        Render Markdown
    """
    if request.method == 'GET':
        return Response(markdown(request.GET['text']))


class CounterViewSet(viewsets.ModelViewSet):
    """
        Manage Counters (api/v1/counter)
    """

    serializer_class = serializers.Counter
    queryset = Counter.objects.all()

    @list_route()
    def bar(self, request):
        """
            Return all counters (api/v1/counter/bar)
        """
        self.queryset = Counter.objects.filter(type="BAR")
        serializer = self.get_serializer(self.queryset, many=True)
        return Response(serializer.data)

    @detail_route()
    def id(self, request, pk=None):
        """
            Get by id (api/v1/{nk}/id)
        """
        self.queryset = get_object_or_404(Counter.objects.filter(id=pk))
        serializer = self.get_serializer(self.queryset)
        return Response(serializer.data)
