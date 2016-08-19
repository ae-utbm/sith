from rest_framework import serializers

from core.models import RealGroup

from api.views import RightModelViewSet


class GroupSerializer(serializers.ModelSerializer):

    class Meta:
        model = RealGroup


class GroupViewSet(RightModelViewSet):
    """
        Manage Groups (api/v1/group/)
    """

    serializer_class = GroupSerializer
    queryset = RealGroup.objects.all()
