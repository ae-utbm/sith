# -*- coding:utf-8 -*-
#
# Copyright 2023 © AE UTBM
# ae@utbm.fr / ae.info@utbm.fr
# All contributors are listed in the CONTRIBUTORS file.
#
# This file is part of the website of the UTBM Student Association (AE UTBM),
# https://ae.utbm.fr.
#
# You can find the whole source code at https://github.com/ae-utbm/sith3
#
# LICENSED UNDER THE GNU GENERAL PUBLIC LICENSE VERSION 3 (GPLv3)
# SEE : https://raw.githubusercontent.com/ae-utbm/sith3/master/LICENSE
# OR WITHIN THE LOCAL FILE "LICENSE"
#
# PREVIOUSLY LICENSED UNDER THE MIT LICENSE,
# SEE : https://raw.githubusercontent.com/ae-utbm/sith3/master/LICENSE.old
# OR WITHIN THE LOCAL FILE "LICENSE.old"
#

from rest_framework import serializers
from rest_framework.decorators import action
from rest_framework.response import Response

from api.views import RightModelViewSet
from counter.models import Counter


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
