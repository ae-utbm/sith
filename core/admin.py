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
from django.contrib.auth.models import Group as AuthGroup
from django.contrib.auth.models import Permission

from core.models import (
    BanGroup,
    Group,
    OperationLog,
    Page,
    QuickUploadImage,
    SithFile,
    User,
    UserBan,
)

admin.site.unregister(AuthGroup)


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ("name", "description", "is_manually_manageable")
    list_filter = ("is_manually_manageable",)
    search_fields = ("name",)
    autocomplete_fields = ("permissions",)


@admin.register(BanGroup)
class BanGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)
    autocomplete_fields = ("permissions",)


class UserBanInline(admin.TabularInline):
    model = UserBan
    extra = 0
    autocomplete_fields = ("ban_group",)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "username", "email", "nick_name")
    autocomplete_fields = (
        "godfathers",
        "home",
        "profile_pict",
        "avatar_pict",
        "scrub_pict",
        "user_permissions",
        "groups",
    )
    inlines = (UserBanInline,)
    search_fields = ["first_name", "last_name", "username"]


@admin.register(UserBan)
class UserBanAdmin(admin.ModelAdmin):
    list_display = ("user", "ban_group", "created_at", "expires_at")
    autocomplete_fields = ("user", "ban_group")


class GroupInline(admin.TabularInline):
    model = Group.permissions.through
    readonly_fields = ("group",)
    extra = 0

    def has_add_permission(self, request, obj):
        return False


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    search_fields = ("codename",)
    inlines = (GroupInline,)


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


@admin.register(OperationLog)
class OperationLogAdmin(admin.ModelAdmin):
    list_display = ("label", "operator", "operation_type", "date")
    search_fields = ("label", "date", "operation_type")
    autocomplete_fields = ("operator",)


@admin.register(QuickUploadImage)
class QuickUploadImageAdmin(admin.ModelAdmin):
    list_display = ("uuid", "uploader", "created_at", "name")
    search_fields = ("uuid", "uploader", "name")
    autocomplete_fields = ("uploader",)
    readonly_fields = ("width", "height", "size")
