from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import viewsets
from rest_framework.decorators import detail_route
from rest_framework.decorators import list_route

from core.templatetags.renderer import markdown
from counter.models import Counter
from core.models import User, Group
from club.models import Club
from api.views import serializers
from api.views import RightManagedModelViewSet

@api_view(['GET'])
def RenderMarkdown(request):
    """
        Render Markdown
    """
    if request.method == 'GET':
        return Response(markdown(request.GET['text']))


class CounterViewSet(RightManagedModelViewSet):
    """
        Manage Counters (api/v1/counter/)
    """

    serializer_class = serializers.CounterRead
    queryset = Counter.objects.all()

    @list_route()
    def bar(self, request):
        """
            Return all bars (api/v1/counter/bar/)
        """
        self.queryset = self.queryset.filter(type="BAR")
        serializer = self.get_serializer(self.queryset, many=True)
        return Response(serializer.data)


class UserViewSet(RightManagedModelViewSet):
    """
        Manage Users (api/v1/user/)
    """

    serializer_class = serializers.UserRead
    queryset = User.objects.all()


class ClubViewSet(RightManagedModelViewSet):
    """
        Manage Clubs (api/v1/club/)
    """

    serializer_class = serializers.ClubRead
    queryset = Club.objects.all()

class GroupViewSet(RightManagedModelViewSet):
    """
        Manage Groups (api/v1/group/)
    """

    serializer_class = serializers.GroupRead
    queryset = Group.objects.all()
