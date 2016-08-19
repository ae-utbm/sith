from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.decorators import list_route

from counter.models import Counter

from api.views import RightModelViewSet


class CounterSerializer(serializers.ModelSerializer):

    is_open = serializers.BooleanField(read_only=True)
    barman_list = serializers.ListField(
        child=serializers.IntegerField()
    )

    class Meta:
        model = Counter
        fields = ('id', 'name', 'type', 'is_open', 'barman_list')


class CounterViewSet(RightModelViewSet):
    """
        Manage Counters (api/v1/counter/)
    """

    serializer_class = CounterSerializer
    queryset = Counter.objects.all()

    @list_route()
    def bar(self, request):
        """
            Return all bars (api/v1/counter/bar/)
        """
        self.queryset = self.queryset.filter(type="BAR")
        serializer = self.get_serializer(self.queryset, many=True)
        return Response(serializer.data)
