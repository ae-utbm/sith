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
from ajax_select import make_ajax_form
from core.models import User, Page, RealGroup, SithFile
from django.contrib.auth.models import Group as AuthGroup
from haystack.admin import SearchModelAdmin


admin.site.unregister(AuthGroup)
admin.site.register(RealGroup)


class UserAdmin(SearchModelAdmin):
    list_display = ["first_name", "last_name", "username", "email", "nick_name"]
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


admin.site.register(User, UserAdmin)


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
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
    form = make_ajax_form(SithFile, {"parent": "files"})  # ManyToManyField
