from rest_framework import serializers

from club.models import Club

from api.views import RightModelViewSet


class ClubSerializer(serializers.ModelSerializer):

    class Meta:
        model = Club
        fields = ('id', 'name', 'unix_name', 'address', 'members')


class ClubViewSet(RightModelViewSet):
    """
        Manage Clubs (api/v1/club/)
    """

    serializer_class = ClubSerializer
    queryset = Club.objects.all()
