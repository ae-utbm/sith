# -*- coding:utf-8 -*
#
# Copyright 2023 © AE UTBM
# ae@utbm.fr / ae.info@utbm.fr
#
# This file is part of the website of the UTBM Student Association (AE UTBM),
# https://ae.utbm.fr.
#
# You can find the source code of the website at https://github.com/ae-utbm/sith3
#
# LICENSED UNDER THE GNU GENERAL PUBLIC LICENSE VERSION 3 (GPLv3)
# SEE : https://raw.githubusercontent.com/ae-utbm/sith3/master/LICENSE
# OR WITHIN THE LOCAL FILE "LICENSE"
#
#

from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.decorators import action

from counter.models import Counter

from api.views import RightModelViewSet


class CounterSerializer(serializers.ModelSerializer):
    is_open = serializers.BooleanField(read_only=True)
    barman_list = serializers.ListField(
        child=serializers.IntegerField(), read_only=True
    )

    class Meta:
        model = Counter
        fields = ("id", "name", "type", "club", "products", "is_open", "barman_list")


class CounterViewSet(RightModelViewSet):
    """
    Manage Counters (api/v1/counter/)
    """

    serializer_class = CounterSerializer
    queryset = Counter.objects.all()

    @action(detail=False)
    def bar(self, request):
        """
        Return all bars (api/v1/counter/bar/)
        """
        self.queryset = self.queryset.filter(type="BAR")
        serializer = self.get_serializer(self.queryset, many=True)
        return Response(serializer.data)
