import datetime

from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import viewsets
from rest_framework.decorators import detail_route
from rest_framework.decorators import list_route

from core.templatetags.renderer import markdown
from counter.models import Counter
from core.models import User, RealGroup
from club.models import Club
from launderette.models import Launderette, Machine, Token

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
        Only show active users
    """

    serializer_class = serializers.UserRead
    queryset = User.objects.filter(is_active=True)

    @list_route()
    def birthday(self, request):
        """
            Return all users born today (api/v1/user/birstdays)
        """
        date = datetime.datetime.today()
        self.queryset = self.queryset.filter(date_of_birth=date)
        serializer = self.get_serializer(self.queryset, many=True)
        return Response(serializer.data)


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
    queryset = RealGroup.objects.all()

class LaunderettePlaceViewSet(RightManagedModelViewSet):
    """
        Manage Launderette (api/v1/launderette/place/)
    """

    serializer_class = serializers.LaunderettePlaceRead
    queryset = Launderette.objects.all()

class LaunderetteMachineViewSet(RightManagedModelViewSet):
    """
        Manage Washing Machines (api/v1/launderette/machine/)
    """

    serializer_class = serializers.LaunderetteMachineRead
    queryset = Machine.objects.all()

class LaunderetteTokenViewSet(RightManagedModelViewSet):
    """
        Manage Launderette's tokens (api/v1/launderette/token/)
    """

    serializer_class = serializers.LaunderetteTokenRead
    queryset = Token.objects.all()

    @list_route()
    def washing(self, request):
        """
            Return all washing tokens (api/v1/launderette/token/washing)
        """
        self.queryset = self.queryset.filter(type='WASHING')
        serializer = self.get_serializer(self.queryset, many=True)
        return Response(serializer.data)

    @list_route()
    def drying(self, request):
        """
            Return all drying tokens (api/v1/launderette/token/drying)
        """
        self.queryset = self.queryset.filter(type='DRYING')
        serializer = self.get_serializer(self.queryset, many=True)
        return Response(serializer.data)

    @list_route()
    def avaliable(self, request):
        """
            Return all avaliable tokens (api/v1/launderette/token/avaliable)
        """
        self.queryset = self.queryset.filter(borrow_date__isnull=True, user__isnull=True)
        serializer = self.get_serializer(self.queryset, many=True)
        return Response(serializer.data)

    @list_route()
    def unavaliable(self, request):
        """
            Return all unavaliable tokens (api/v1/launderette/token/unavaliable)
        """
        self.queryset = self.queryset.filter(borrow_date__isnull=False, user__isnull=False)
        serializer = self.get_serializer(self.queryset, many=True)
        return Response(serializer.data)
