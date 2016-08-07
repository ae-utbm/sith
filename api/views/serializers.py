from rest_framework import serializers
from counter.models import Counter
from core.models import User, RealGroup
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
        fields = ('id', 'first_name', 'last_name', 'email',
                  'date_of_birth', 'nick_name', 'is_active', 'date_joined')


class ClubRead(serializers.ModelSerializer):

    class Meta:
        model = Club
        fields = ('id', 'name', 'unix_name', 'address', 'members')


class GroupRead(serializers.ModelSerializer):

    class Meta:
        model = RealGroup
