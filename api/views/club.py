# -*- coding:utf-8 -*
#
# Copyright 2016,2017
# - Skia <skia@libskia.so>
#
# Ce fichier fait partie du site de l'Association des Étudiants de l'UTBM,
# http://ae.utbm.fr.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License a published by the Free Software
# Foundation; either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Sofware Foundation, Inc., 59 Temple
# Place - Suite 330, Boston, MA 02111-1307, USA.
#
#

from rest_framework.response import Response
from rest_framework import serializers
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import StaticHTMLRenderer

from django.conf import settings
from django.core.exceptions import PermissionDenied

from club.models import Club, Mailing

from api.views import RightModelViewSet


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
