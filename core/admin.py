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
from django.contrib.auth.models import Group as AuthGroup

from core.models import Group, Page, SithFile, User

admin.site.unregister(AuthGroup)


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "is_meta")
    list_filter = ("is_meta",)
    search_fields = ("name",)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "username", "email", "nick_name")
    autocomplete_fields = (
        "godfathers",
        "home",
        "profile_pict",
        "avatar_pict",
        "scrub_pict",
    )
    search_fields = ["first_name", "last_name", "username"]


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ("name", "_full_name", "owner_group")
    search_fields = ("name",)
    autocomplete_fields = ("lock_user", "owner_group", "edit_groups", "view_groups")


@admin.register(SithFile)
class SithFileAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "size", "date", "is_in_sas")
    autocomplete_fields = ("parent", "owner", "moderator")
    search_fields = ("name", "parent__name")
