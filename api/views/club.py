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

from django.conf import settings
from django.core.exceptions import PermissionDenied
from rest_framework import serializers
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import StaticHTMLRenderer
from rest_framework.response import Response

from api.views import RightModelViewSet
from club.models import Club, Mailing


class ClubSerializer(serializers.ModelSerializer):
    class Meta:
        model = Club
        fields = ("id", "name", "unix_name", "address", "members")


class ClubViewSet(RightModelViewSet):
    """
    Manage Clubs (api/v1/club/)
    """

    serializer_class = ClubSerializer
    queryset = Club.objects.all()


@api_view(["GET"])
@renderer_classes((StaticHTMLRenderer,))
def FetchMailingLists(request):
    key = request.GET.get("key", "")
    if key != settings.SITH_MAILING_FETCH_KEY:
        raise PermissionDenied
    data = ""
    for mailing in Mailing.objects.filter(
        is_moderated=True, club__is_active=True
    ).all():
        data += mailing.fetch_format() + "\n"
    return Response(data)
