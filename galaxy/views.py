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

from django.db.models import Case, F, Q, Value, When
from django.db.models.functions import Concat
from django.http import Http404, JsonResponse
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, View

from core.models import User
from core.views import (
    CanViewMixin,
    FormerSubscriberMixin,
    UserTabsMixin,
)
from galaxy.models import Galaxy, GalaxyLane


class GalaxyUserView(CanViewMixin, UserTabsMixin, DetailView):
    model = User
    pk_url_kwarg = "user_id"
    template_name = "galaxy/user.jinja"
    current_tab = "galaxy"

    def get_object(self, *args, **kwargs):
        user: User = super(GalaxyUserView, self).get_object(*args, **kwargs)
        if user.current_star is None:
            raise Http404(_("This citizen has not yet joined the galaxy"))
        return user

    def get_context_data(self, **kwargs):
        kwargs = super(GalaxyUserView, self).get_context_data(**kwargs)
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
