import datetime

from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.decorators import list_route

from core.models import User

from api.views import RightModelViewSet


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email',
                  'date_of_birth', 'nick_name', 'is_active', 'date_joined')


class UserViewSet(RightModelViewSet):
    """
        Manage Users (api/v1/user/)
        Only show active users
    """

    serializer_class = UserSerializer
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
