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

from club.models import Club, Membership


@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ("name", "slug_name", "parent", "is_active")
    search_fields = ("name", "slug_name")
    autocomplete_fields = (
        "parent",
        "board_group",
        "members_group",
        "home",
        "page",
    )


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "club", "role", "start_date", "end_date")
    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "club__name",
    )
    autocomplete_fields = ("user",)
