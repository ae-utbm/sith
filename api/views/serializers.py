from rest_framework import serializers
from counter.models import Counter


class Counter(serializers.ModelSerializer):

    is_open = serializers.BooleanField(read_only=True)
    barman_list = serializers.ListField(
            child = serializers.IntegerField()
            )

    class Meta:
        model = Counter
        fields = ('id', 'name', 'type', 'is_open', 'barman_list')

