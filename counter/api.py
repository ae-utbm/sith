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
from django.conf import settings
from django.db.models import F
from ninja import Query
from ninja_extra import ControllerBase, api_controller, paginate, route
from ninja_extra.pagination import PageNumberPaginationExtra
from ninja_extra.schemas import PaginatedResponseSchema

from core.api_permissions import CanAccessLookup, CanView, IsInGroup, IsRoot
from counter.models import Counter, Product
from counter.schemas import (
    CounterFilterSchema,
    CounterSchema,
    ProductFilterSchema,
    ProductSchema,
    SimpleProductSchema,
    SimplifiedCounterSchema,
)


@api_controller("/counter")
class CounterController(ControllerBase):
    @route.get("", response=list[CounterSchema], permissions=[IsRoot])
    def fetch_all(self):
        return Counter.objects.annotate_is_open()

    @route.get("{counter_id}/", response=CounterSchema, permissions=[CanView])
    def fetch_one(self, counter_id: int):
        return self.get_object_or_exception(
            Counter.objects.annotate_is_open(), pk=counter_id
        )

    @route.get("bar/", response=list[CounterSchema], permissions=[CanView])
    def fetch_bars(self):
        counters = list(Counter.objects.annotate_is_open().filter(type="BAR"))
        for c in counters:
            self.check_object_permissions(c)
        return counters

    @route.get(
        "/search",
        response=PaginatedResponseSchema[SimplifiedCounterSchema],
        permissions=[CanAccessLookup],
    )
    @paginate(PageNumberPaginationExtra, page_size=50)
    def search_counter(self, filters: Query[CounterFilterSchema]):
        return filters.filter(Counter.objects.all())


@api_controller("/product")
class ProductController(ControllerBase):
    @route.get(
        "/search",
        response=PaginatedResponseSchema[SimpleProductSchema],
        permissions=[CanAccessLookup],
    )
    @paginate(PageNumberPaginationExtra, page_size=50)
    def search_products(self, filters: Query[ProductFilterSchema]):
        return filters.filter(
            Product.objects.order_by(
                F("product_type__order").asc(nulls_last=True),
                "product_type",
                "name",
            ).values()
        )

    @route.get(
        "/search/detailed",
        response=PaginatedResponseSchema[ProductSchema],
        permissions=[
            IsRoot
            | IsInGroup(settings.SITH_GROUP_COUNTER_ADMIN_ID)
            | IsInGroup(settings.SITH_GROUP_ACCOUNTING_ADMIN_ID)
        ],
        url_name="search_products_detailed",
    )
    @paginate(PageNumberPaginationExtra, page_size=50)
    def search_products_detailed(self, filters: Query[ProductFilterSchema]):
        """Get the detailed information about the products."""
        return filters.filter(
            Product.objects.select_related("club")
            .prefetch_related("buying_groups")
            .select_related("product_type")
            .order_by(
                F("product_type__order").asc(nulls_last=True),
                "product_type",
                "name",
            )
        )
