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
from ajax_select import make_ajax_form
from django.contrib import admin
from haystack.admin import SearchModelAdmin

from counter.models import *


@admin.register(Product)
class ProductAdmin(SearchModelAdmin):
    list_display = (
        "name",
        "code",
        "product_type",
        "selling_price",
        "profit",
        "archived",
    )
    search_fields = ("name", "code")


@admin.register(Customer)
class CustomerAdmin(SearchModelAdmin):
    list_display = ("user", "account_id", "amount")
    search_fields = (
        "account_id",
        "user__username",
        "user__first_name",
        "user__last_name",
    )
    form = make_ajax_form(Customer, {"user": "users"})


@admin.register(BillingInfo)
class BillingInfoAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "address_1", "city", "country")


@admin.register(Counter)
class CounterAdmin(admin.ModelAdmin):
    list_display = ("name", "club", "type")
    form = make_ajax_form(
        Counter,
        {
            "products": "products",
            "sellers": "users",
        },
    )


@admin.register(Refilling)
class RefillingAdmin(SearchModelAdmin):
    list_display = ("customer", "amount", "counter", "payment_method", "date")
    search_fields = (
        "customer__user__username",
        "customer__user__first_name",
        "customer__user__last_name",
        "customer__account_id",
        "counter__name",
    )
    form = make_ajax_form(
        Refilling,
        {
            "customer": "customers",
            "operator": "users",
        },
    )


@admin.register(Selling)
class SellingAdmin(SearchModelAdmin):
    list_display = ("customer", "label", "unit_price", "quantity", "counter", "date")
    search_fields = (
        "customer__user__username",
        "customer__user__first_name",
        "customer__user__last_name",
        "customer__account_id",
        "counter__name",
    )
    form = make_ajax_form(
        Selling,
        {
            "customer": "customers",
            "seller": "users",
        },
    )


@admin.register(Permanency)
class PermanencyAdmin(SearchModelAdmin):
    list_display = ("user", "counter", "start", "duration")
    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "counter__name",
    )
    form = make_ajax_form(Permanency, {"user": "users"})


@admin.register(ProductType)
class ProductTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "priority")


@admin.register(CashRegisterSummary)
class CashRegisterSummaryAdmin(SearchModelAdmin):
    list_display = ("user", "counter", "date")
    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "counter__name",
    )
    form = make_ajax_form(CashRegisterSummary, {"user": "users"})


@admin.register(Eticket)
class EticketAdmin(SearchModelAdmin):
    list_display = ("product", "event_date", "event_title")
    search_fields = ("product__name", "event_title")
