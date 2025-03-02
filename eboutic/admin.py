#
# Copyright 2023 © AE UTBM
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
from django.contrib import admin
from django.db.models import F, Sum

from eboutic.models import Basket, BasketItem, Invoice, InvoiceItem


@admin.register(Basket)
class BasketAdmin(admin.ModelAdmin):
    list_display = ("user", "date", "total")
    autocomplete_fields = ("user",)

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(
                total=Sum(
                    F("items__quantity") * F("items__product_unit_price"), default=0
                )
            )
        )


@admin.register(BasketItem)
class BasketItemAdmin(admin.ModelAdmin):
    list_display = ("basket", "product_name", "product_unit_price", "quantity")
    search_fields = ("product_name",)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("user", "date", "validated")
    search_fields = ("user__username", "user__first_name", "user__last_name")
    autocomplete_fields = ("user",)


@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ("invoice", "product_name", "product_unit_price", "quantity")
    search_fields = ("product_name",)
