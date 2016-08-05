from rest_framework import serializers
from counter.models import Counter


class Counter(serializers.ModelSerializer):

    is_open = serializers.BooleanField(read_only=True)

    class Meta:
        model = Counter
        fields = ('id', 'name', 'is_open')
