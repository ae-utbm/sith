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
from django.shortcuts import get_object_or_404
from ninja import Query
from ninja.security import SessionAuth
from ninja_extra import ControllerBase, api_controller, paginate, route
from ninja_extra.pagination import PageNumberPaginationExtra
from ninja_extra.schemas import PaginatedResponseSchema

from api.auth import ApiKeyAuth
from api.permissions import CanAccessLookup, CanView, IsInGroup, IsRoot
from counter.models import Counter, Product, ProductType
from counter.schemas import (
    CounterFilterSchema,
    CounterSchema,
    ProductFilterSchema,
    ProductSchema,
    ProductTypeSchema,
    ReorderProductTypeSchema,
    SimpleProductSchema,
    SimplifiedCounterSchema,
)

IsCounterAdmin = (
    IsRoot
    | IsInGroup(settings.SITH_GROUP_COUNTER_ADMIN_ID)
    | IsInGroup(settings.SITH_GROUP_ACCOUNTING_ADMIN_ID)
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
        auth=[ApiKeyAuth(), SessionAuth()],
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
        auth=[ApiKeyAuth(), SessionAuth()],
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
        permissions=[IsCounterAdmin],
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


@api_controller("/product-type", permissions=[IsCounterAdmin])
class ProductTypeController(ControllerBase):
    @route.get("", response=list[ProductTypeSchema], url_name="fetch_product_types")
    def fetch_all(self):
        return ProductType.objects.order_by("order")

    @route.patch("/{type_id}/move", url_name="reorder_product_type")
    def reorder(self, type_id: int, other_id: Query[ReorderProductTypeSchema]):
        """Change the order of a product type.

        To use this route, give either the id of the product type
        this one should be above of,
        of the id of the product type this one should be below of.

        Order affects the display order of the product types.

        Examples:
            ```
            GET /api/counter/product-type
            => [<1: type A>, <2: type B>, <3: type C>]

            PATCH /api/counter/product-type/3/move?below=1

            GET /api/counter/product-type
            => [<1: type A>, <3: type C>, <2: type B>]
            ```
        """
        product_type: ProductType = self.get_object_or_exception(
            ProductType, pk=type_id
        )
        other = get_object_or_404(ProductType, pk=other_id.above or other_id.below)
        if other_id.below is not None:
            product_type.below(other)
        else:
            product_type.above(other)
