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
# SEE : https://raw.githubusercontent.com/ae-utbm/sith/master/LICENSE
# OR WITHIN THE LOCAL FILE "LICENSE"
#
#

from ninja import Query
from ninja_extra import ControllerBase, api_controller, paginate, route
from ninja_extra.pagination import PageNumberPaginationExtra
from ninja_extra.schemas import PaginatedResponseSchema

from core.api_permissions import CanView, IsOldSubscriber, IsRoot
from counter.models import Counter, Permanency
from counter.schemas import CounterSchema, PermanencyFilterSchema, PermanencySchema


@api_controller("/counter")
class CounterController(ControllerBase):
    @route.get("", response=list[CounterSchema], permissions=[IsRoot])
    def fetch_all(self):
        return Counter.objects.all()

    @route.get("{counter_id}/", response=CounterSchema, permissions=[CanView])
    def fetch_one(self, counter_id: int):
        return self.get_object_or_exception(Counter.objects.all(), pk=counter_id)

    @route.get("bar/", response=list[CounterSchema], permissions=[CanView])
    def fetch_bars(self):
        counters = list(Counter.objects.all().filter(type="BAR"))
        for c in counters:
            self.check_object_permissions(c)
        return counters


@api_controller("/permanency")
class PermanencyController(ControllerBase):
    @route.get(
        "",
        response=PaginatedResponseSchema[PermanencySchema],
        permissions=[IsOldSubscriber],
        exclude_none=True,
    )
    @paginate(PageNumberPaginationExtra, page_size=100)
    def fetch_permanancies(self, filters: Query[PermanencyFilterSchema]):
        return filters.filter(Permanency.objects.all()).distinct().order_by("-start")
