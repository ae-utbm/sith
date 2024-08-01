#
# Copyright 2023 © AE UTBM
# ae@utbm.fr / ae.info@utbm.fr
#
# This file is part of the website of the UTBM Student Association (AE UTBM),
# https://ae.utbm.fr.
#
# You can find the source code of the website at https://github.com/ae-utbm/sith3
#
# LICENSED UNDER THE GNU GENERAL PUBLIC LICENSE VERSION 3 (GPLv3)
# SEE : https://raw.githubusercontent.com/ae-utbm/sith3/master/LICENSE
# OR WITHIN THE LOCAL FILE "LICENSE"
#
#
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
    autocomplete_fields = ("user",)


@admin.register(Slot)
class SlotAdmin(admin.ModelAdmin):
    list_display = ("machine", "user", "start_date")
    autocomplete_fields = ("user",)
