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

from launderette.models import *


@admin.register(Launderette)
class LaunderetteAdmin(admin.ModelAdmin):
    list_display = ("name", "counter")


@admin.register(Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display = ("name", "launderette", "type", "is_working")


@admin.register(Token)
class TokenAdmin(admin.ModelAdmin):
    list_display = ("name", "launderette", "type", "user")
    form = make_ajax_form(Token, {"user": "users"})


@admin.register(Slot)
class SlotAdmin(admin.ModelAdmin):
    list_display = ("machine", "user", "start_date")
    form = make_ajax_form(Slot, {"user": "users"})
