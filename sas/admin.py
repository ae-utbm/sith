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

from sas.models import Album, PeoplePictureRelation, Picture, PictureModerationRequest


@admin.register(Picture)
class PictureAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "date", "size", "is_moderated")
    search_fields = ("name",)
    autocomplete_fields = ("owner", "parent", "edit_groups", "view_groups", "moderator")


@admin.register(PeoplePictureRelation)
class PeoplePictureRelationAdmin(admin.ModelAdmin):
    list_display = ("picture", "user")
    autocomplete_fields = ("picture", "user")


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "date", "owner", "is_moderated")
    search_fields = ("name",)
    autocomplete_fields = ("owner", "parent", "edit_groups", "view_groups")


@admin.register(PictureModerationRequest)
class PictureModerationRequestAdmin(admin.ModelAdmin):
    list_display = ("author", "picture", "created_at")
    search_fields = ("author", "picture")
    autocomplete_fields = ("author", "picture")
