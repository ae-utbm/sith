# -*- coding:utf-8 -*
#
# Copyright 2016,2017
# - Skia <skia@libskia.so>
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
