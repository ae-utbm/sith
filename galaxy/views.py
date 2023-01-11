# -*- coding:utf-8 -*
#
# Copyright 2023
# - Skia <skia@hya.sk>
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

from django.views.generic import DetailView, View
from django.http import JsonResponse

from core.views import (
    CanViewMixin,
    FormerSubscriberMixin,
)
from core.models import User
from core.views import UserTabsMixin
from galaxy.models import Galaxy


class GalaxyUserView(CanViewMixin, UserTabsMixin, DetailView):
    model = User
    pk_url_kwarg = "user_id"
    template_name = "galaxy/user.jinja"
    current_tab = "galaxy"


class GalaxyDataView(FormerSubscriberMixin, View):
    def get(self, request, *args, **kwargs):
        return JsonResponse(Galaxy().as_dict())
