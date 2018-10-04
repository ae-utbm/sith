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

from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.decorators import list_route

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

    @list_route()
    def bar(self, request):
        """
            Return all bars (api/v1/counter/bar/)
        """
        self.queryset = self.queryset.filter(type="BAR")
        serializer = self.get_serializer(self.queryset, many=True)
        return Response(serializer.data)
