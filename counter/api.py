#
# Copyright 2024 AE UTBM
# ae@utbm.fr / ae.info@utbm.fr
#
# This file is part of the website of the UTBM Student Association (AE UTBM),
# https://ae.utbm.fr.
#
# You can find the source code of the website at https://github.com/ae-utbm/sith
#
# LICENSED UNDER THE GNU GENERAL PUBLIC LICENSE VERSION 3 (GPLv3)
# SEE : https://raw.githubusercontent.com/ae-utbm/sith3/master/LICENSE
# OR WITHIN THE LOCAL FILE "LICENSE"
#
#
from ninja_extra import ControllerBase, api_controller, route

from core.api_permissions import CanView, IsRoot
from counter.models import Counter
from counter.schemas import CounterSchema


@api_controller("/counter")
class CounterController(ControllerBase):
    @route.get("", response=list[CounterSchema], permissions=[IsRoot])
    def fetch_all(self):
        return Counter.objects.all()

    @route.get("{counter_id}/", response=CounterSchema, permissions=[CanView])
    def fetch_one(self, counter_id: int):
        return self.get_object_or_exception(Counter, pk=counter_id)

    @route.get("bar/", response=list[CounterSchema], permissions=[CanView])
    def fetch_bars(self):
        counters = list(Counter.objects.filter(type="BAR"))
        for c in counters:
            self.check_object_permissions(c)
        return counters
