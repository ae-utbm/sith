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

from django.contrib import admin
from haystack.admin import SearchModelAdmin

from counter.models import *


class ProductAdmin(SearchModelAdmin):
    search_fields = ["name", "code"]


class CustomerAdmin(SearchModelAdmin):
    search_fields = ["account_id"]


@admin.register(BillingInfo)
class BillingInfoAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "address_1", "city", "country")


admin.site.register(Customer, CustomerAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(ProductType)
admin.site.register(Counter)
admin.site.register(Refilling)
admin.site.register(Selling)
admin.site.register(Permanency)
admin.site.register(CashRegisterSummary)
admin.site.register(Eticket)
