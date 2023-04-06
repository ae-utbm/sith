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
from launderette.models import Launderette, Machine, Token


class LaunderettePlaceSerializer(serializers.ModelSerializer):
    machine_list = serializers.ListField(
        child=serializers.IntegerField(), read_only=True
    )
    token_list = serializers.ListField(child=serializers.IntegerField(), read_only=True)

    class Meta:
        model = Launderette
        fields = (
            "id",
            "name",
            "counter",
            "machine_list",
            "token_list",
            "get_absolute_url",
        )


class LaunderetteMachineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Machine
        fields = ("id", "name", "type", "is_working", "launderette")


class LaunderetteTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Token
        fields = (
            "id",
            "name",
            "type",
            "launderette",
            "borrow_date",
            "user",
            "is_avaliable",
        )


class LaunderettePlaceViewSet(RightModelViewSet):
    """
    Manage Launderette (api/v1/launderette/place/)
    """

    serializer_class = LaunderettePlaceSerializer
    queryset = Launderette.objects.all()


class LaunderetteMachineViewSet(RightModelViewSet):
    """
    Manage Washing Machines (api/v1/launderette/machine/)
    """

    serializer_class = LaunderetteMachineSerializer
    queryset = Machine.objects.all()


class LaunderetteTokenViewSet(RightModelViewSet):
    """
    Manage Launderette's tokens (api/v1/launderette/token/)
    """

    serializer_class = LaunderetteTokenSerializer
    queryset = Token.objects.all()

    @action(detail=False)
    def washing(self, request):
        """
        Return all washing tokens (api/v1/launderette/token/washing)
        """
        self.queryset = self.queryset.filter(type="WASHING")
        serializer = self.get_serializer(self.queryset, many=True)
        return Response(serializer.data)

    @action(detail=False)
    def drying(self, request):
        """
        Return all drying tokens (api/v1/launderette/token/drying)
        """
        self.queryset = self.queryset.filter(type="DRYING")
        serializer = self.get_serializer(self.queryset, many=True)
        return Response(serializer.data)

    @action(detail=False)
    def avaliable(self, request):
        """
        Return all avaliable tokens (api/v1/launderette/token/avaliable)
        """
        self.queryset = self.queryset.filter(
            borrow_date__isnull=True, user__isnull=True
        )
        serializer = self.get_serializer(self.queryset, many=True)
        return Response(serializer.data)

    @action(detail=False)
    def unavaliable(self, request):
        """
        Return all unavaliable tokens (api/v1/launderette/token/unavaliable)
        """
        self.queryset = self.queryset.filter(
            borrow_date__isnull=False, user__isnull=False
        )
        serializer = self.get_serializer(self.queryset, many=True)
        return Response(serializer.data)
