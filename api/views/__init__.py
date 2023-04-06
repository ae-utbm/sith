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

from django.core.exceptions import PermissionDenied
from django.db.models.query import QuerySet
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.views import can_edit, can_view


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
from .club import *
from .counter import *
from .group import *
from .launderette import *
from .sas import *
from .user import *
from .uv import *
