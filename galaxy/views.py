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

from django.db.models import Case, F, Q, Value, When
from django.db.models.functions import Concat
from django.http import Http404, JsonResponse
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, View

from core.auth.mixins import CanViewMixin, FormerSubscriberMixin
from core.models import User
from core.views import UserTabsMixin
from galaxy.models import Galaxy, GalaxyLane


class GalaxyUserView(CanViewMixin, UserTabsMixin, DetailView):
    model = User
    pk_url_kwarg = "user_id"
    template_name = "galaxy/user.jinja"
    current_tab = "galaxy"

    def get_object(self, *args, **kwargs):
        user: User = super().get_object(*args, **kwargs)
        if user.current_star is None:
            raise Http404(_("This citizen has not yet joined the galaxy"))
        return user

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        kwargs["lanes"] = (
            GalaxyLane.objects.filter(
                Q(star1=self.object.current_star) | Q(star2=self.object.current_star)
            )
            .order_by("distance")
            .annotate(
                other_star_id=Case(
                    When(star1=self.object.current_star, then=F("star2__owner__id")),
                    default=F("star1__owner__id"),
                ),
                other_star_mass=Case(
                    When(star1=self.object.current_star, then=F("star2__mass")),
                    default=F("star1__mass"),
                ),
                other_star_name=Case(
                    When(
                        star1=self.object.current_star,
                        then=Case(
                            When(
                                star2__owner__nick_name=None,
                                then=Concat(
                                    F("star2__owner__first_name"),
                                    Value(" "),
                                    F("star2__owner__last_name"),
                                ),
                            )
                        ),
                    ),
                    default=Case(
                        When(
                            star1__owner__nick_name=None,
                            then=Concat(
                                F("star1__owner__first_name"),
                                Value(" "),
                                F("star1__owner__last_name"),
                            ),
                        )
                    ),
                ),
            )
            .select_related("star1", "star2")
        )
        return kwargs


class GalaxyDataView(FormerSubscriberMixin, View):
    def get(self, request, *args, **kwargs):
        return JsonResponse(Galaxy.get_current_galaxy().state)
