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
from django.contrib.auth.models import Group as AuthGroup
from haystack.admin import SearchModelAdmin

from core.models import MetaGroup, Page, RealGroup, SithFile, User

admin.site.unregister(AuthGroup)
admin.site.register(MetaGroup)
admin.site.register(RealGroup)


@admin.register(User)
class UserAdmin(SearchModelAdmin):
    list_display = ("first_name", "last_name", "username", "email", "nick_name")
    form = make_ajax_form(
        User,
        {
            "godfathers": "users",
            "home": "files",  # ManyToManyField
            "profile_pict": "files",  # ManyToManyField
            "avatar_pict": "files",  # ManyToManyField
            "scrub_pict": "files",  # ManyToManyField
        },
    )
    search_fields = ["first_name", "last_name", "username"]


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ("name", "_full_name", "owner_group")
    form = make_ajax_form(
        Page,
        {
            "lock_user": "users",
            "owner_group": "groups",
            "edit_groups": "groups",
            "view_groups": "groups",
        },
    )


@admin.register(SithFile)
class SithFileAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "size", "date", "is_in_sas")
    form = make_ajax_form(
        SithFile,
        {
            "parent": "files",
            "owner": "users",
            "moderator": "users",
        },
    )  # ManyToManyField
