from rest_framework import serializers
from counter.models import Counter
from core.models import User, Group
from club.models import Club


class CounterRead(serializers.ModelSerializer):

    is_open = serializers.BooleanField(read_only=True)
    barman_list = serializers.ListField(
            child=serializers.IntegerField()
            )

    class Meta:
        model = Counter
        fields = ('id', 'name', 'type', 'is_open', 'barman_list')


class UserRead(serializers.ModelSerializer):

    class Meta:
        model = User


class ClubRead(serializers.ModelSerializer):

    class Meta:
        model = Club


class GroupRead(serializers.ModelSerializer):

    class Meta:
        model = Group
