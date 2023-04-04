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

from rest_framework.response import Response
from rest_framework import viewsets
from django.core.exceptions import PermissionDenied
from rest_framework.decorators import action
from django.db.models.query import QuerySet

from core.views import can_view, can_edit


def check_if(obj, user, test):
    """
    Detect if it's a single object or a queryset
    aply a given test on individual object and return global permission
    """
    if isinstance(obj, QuerySet):
        for o in obj:
            if test(o, user) is False:
                return False
        return True
    else:
        return test(obj, user)


class ManageModelMixin:
    @action(detail=True)
    def id(self, request, pk=None):
        """
        Get by id (api/v1/router/{pk}/id/)
        """
        self.queryset = get_object_or_404(self.queryset.filter(id=pk))
        serializer = self.get_serializer(self.queryset)
        return Response(serializer.data)


class RightModelViewSet(ManageModelMixin, viewsets.ModelViewSet):
    def dispatch(self, request, *arg, **kwargs):
        res = super(RightModelViewSet, self).dispatch(request, *arg, **kwargs)
        obj = self.queryset
        user = self.request.user
        try:
            if request.method == "GET" and check_if(obj, user, can_view):
                return res
            if request.method != "GET" and check_if(obj, user, can_edit):
                return res
        except:
            pass  # To prevent bug with Anonymous user
        raise PermissionDenied


from .api import *
from .counter import *
from .user import *
from .club import *
from .group import *
from .launderette import *
from .uv import *
from .sas import *
