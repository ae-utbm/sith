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
from haystack.admin import SearchModelAdmin

from counter.models import (
    AccountDump,
    BillingInfo,
    CashRegisterSummary,
    Counter,
    Customer,
    Eticket,
    Permanency,
    Product,
    ProductType,
    Refilling,
    ReturnableProduct,
    Selling,
)


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
    list_select_related = ("product_type",)
    search_fields = ("name", "code")


@admin.register(ReturnableProduct)
class ReturnableProductAdmin(admin.ModelAdmin):
    list_display = ("product", "returned_product", "max_return")
    search_fields = (
        "product__name",
        "product__code",
        "returned_product__name",
        "returned_product__code",
    )
    autocomplete_fields = ("product", "returned_product")


@admin.register(Customer)
class CustomerAdmin(SearchModelAdmin):
    list_display = ("user", "account_id", "amount")
    search_fields = (
        "account_id",
        "user__username",
        "user__first_name",
        "user__last_name",
    )
    autocomplete_fields = ("user",)


@admin.register(BillingInfo)
class BillingInfoAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "address_1", "city", "country")
    autocomplete_fields = ("customer",)


@admin.register(AccountDump)
class AccountDumpAdmin(admin.ModelAdmin):
    date_hierarchy = "warning_mail_sent_at"
    list_display = (
        "customer",
        "warning_mail_sent_at",
        "warning_mail_error",
        "dump_operation__date",
        "amount",
    )
    list_select_related = ("customer", "customer__user", "dump_operation")
    autocomplete_fields = ("customer", "dump_operation")
    list_filter = ("warning_mail_error",)


@admin.register(Counter)
class CounterAdmin(admin.ModelAdmin):
    list_display = ("name", "club", "type")
    autocomplete_fields = ("products", "sellers")


@admin.register(Refilling)
class RefillingAdmin(SearchModelAdmin):
    list_display = ("customer", "amount", "counter", "payment_method", "date")
    autocomplete_fields = ("customer", "operator")
    search_fields = (
        "customer__user__username",
        "customer__user__first_name",
        "customer__user__last_name",
        "customer__account_id",
        "counter__name",
    )
    list_filter = (("counter", admin.RelatedOnlyFieldListFilter),)
    date_hierarchy = "date"


@admin.register(Selling)
class SellingAdmin(SearchModelAdmin):
    list_display = ("customer", "label", "unit_price", "quantity", "counter", "date")
    list_select_related = ("customer", "customer__user", "counter")
    search_fields = (
        "customer__user__username",
        "customer__user__first_name",
        "customer__user__last_name",
        "customer__account_id",
        "counter__name",
    )
    autocomplete_fields = ("customer", "seller")
    list_filter = (("counter", admin.RelatedOnlyFieldListFilter),)
    date_hierarchy = "date"


@admin.register(Permanency)
class PermanencyAdmin(SearchModelAdmin):
    list_display = ("user", "counter", "start", "duration")
    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "counter__name",
    )
    autocomplete_fields = ("user",)


@admin.register(ProductType)
class ProductTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "order")


@admin.register(CashRegisterSummary)
class CashRegisterSummaryAdmin(SearchModelAdmin):
    list_display = ("user", "counter", "date")
    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "counter__name",
    )
    autocomplete_fields = ("user",)


@admin.register(Eticket)
class EticketAdmin(SearchModelAdmin):
    list_display = ("product", "event_date", "event_title")
    search_fields = ("product__name", "event_title")
