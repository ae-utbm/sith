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
from enum import IntEnum

from django.conf import settings
from django.db.models import F
from django.shortcuts import get_object_or_404
from ninja import Query, Schema
from ninja.security import SessionAuth
from ninja_extra import ControllerBase, api_controller, paginate, permissions, route
from ninja_extra.pagination import PageNumberPaginationExtra
from ninja_extra.schemas import PaginatedResponseSchema
from typing import List, Dict

from api.auth import ApiKeyAuth
from api.permissions import CanAccessLookup, CanView, IsInGroup, IsRoot
from counter.models import Counter, Product, ProductType, User
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


class SellerIdsSchema(Schema):
    user_ids: List[int]


class SellerIdsResponse(Schema):
    added_ids: List[int]
    not_existing_ids: List[int]


class SellerIdsRemoveResponse(Schema):
    removed_ids: List[int]
    not_existing_ids: List[int]


class SellerCounterOrUserNotFoundErrorCode(IntEnum):
    COUNTER_NOT_FOUND = 1  # 404: Counter not found
    USER_NOT_FOUND = 2     # 404: User(s) not found or not sellers


class SellerCounterOrUserNotFoundResponse(Schema):
    """
    Response schema for not found errors.
    code (SellerCounterOrUserNotFoundErrorCode):
      COUNTER_NOT_FOUND (1): Counter not found (404)
      USER_NOT_FOUND (2): User(s) not found or not sellers (404)
    detail (str): Human readable error message.
    """
    code: SellerCounterOrUserNotFoundErrorCode
    detail: str


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

    @route.post(
        "{counter_id}/seller/add",
        response={200: SellerIdsResponse, 404: SellerCounterOrUserNotFoundResponse},
        permissions=[IsCounterAdmin],
        summary="Add sellers to a counter",
        description="Add one or more users as sellers to the specified counter.\n\n"
                    "Error codes:\n\n"
                    "- 404: Counter not found (code=1).\n\n"
                    "- 404: User(s) not found or not sellers (code=2)."
    )
    def add_sellers_to_counter(self, request, counter_id: int, data: SellerIdsSchema):
        try:
            counter = Counter.objects.get(pk=counter_id)
        except Counter.DoesNotExist:
            return 404, {"detail": "Counter does not exist.", "code": SellerCounterOrUserNotFoundErrorCode.COUNTER_NOT_FOUND}
        added = []
        not_existing = []
        for user_id in data.user_ids:
            try:
                user = User.objects.get(pk=user_id)
                counter.sellers.add(user)
                added.append(user_id)
            except User.DoesNotExist:
                not_existing.append(user_id)
                continue
        if not added and not_existing:
            return 404, {"detail": "No sellers were added. All user IDs not found.", "code": SellerCounterOrUserNotFoundErrorCode.USER_NOT_FOUND}
        return {"added_ids": added, "not_existing_ids": not_existing}

    @route.post(
        "{counter_id}/seller/remove",
        response={200: SellerIdsRemoveResponse, 404: SellerCounterOrUserNotFoundResponse},
        permissions=[IsCounterAdmin],
        summary="Remove sellers from a counter",
        description="Remove one or more users from the sellers of the specified counter.\n\n"
                    "Error codes:\n\n"
                    "- 404: Counter not found (code=1).\n\n"
    )
    def remove_sellers_from_counter(self, request, counter_id: int, data: SellerIdsSchema):
        try:
            counter = Counter.objects.get(pk=counter_id)
        except Counter.DoesNotExist:
            return 404, {"detail": "Counter does not exist.", "code": SellerCounterOrUserNotFoundErrorCode.COUNTER_NOT_FOUND}
        removed = []
        not_existing = []
        for user_id in data.user_ids:
            try:
                user = User.objects.get(pk=user_id)
                if counter.sellers.filter(pk=user.pk).exists():
                    counter.sellers.remove(user)  # On retire juste le lien seller<->counter
                    removed.append(user_id)
                else:
                    not_existing.append(user_id)
            except User.DoesNotExist:
                not_existing.append(user_id)
                continue
        if not removed and not_existing:
            return 404, {"detail": "No sellers were removed. All user IDs not found or not sellers.", "code": SellerCounterOrUserNotFoundErrorCode.USER_NOT_FOUND}
        return {"removed_ids": removed, "not_existing_ids": not_existing}

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
