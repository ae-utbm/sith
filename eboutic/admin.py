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

from eboutic.models import *


@admin.register(Basket)
class BasketAdmin(admin.ModelAdmin):
    list_display = ("user", "date", "get_total")
    form = make_ajax_form(Basket, {"user": "users"})


@admin.register(BasketItem)
class BasketItemAdmin(admin.ModelAdmin):
    list_display = ("basket", "product_name", "product_unit_price", "quantity")
    search_fields = ("product_name",)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("user", "date", "validated")
    search_fields = ("user__username", "user__first_name", "user__last_name")
    form = make_ajax_form(Invoice, {"user": "users"})


@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ("invoice", "product_name", "product_unit_price", "quantity")
    search_fields = ("product_name",)
