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

from sas.models import Album, PeoplePictureRelation, Picture


@admin.register(Picture)
class PictureAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "date", "size", "is_moderated")
    search_fields = ("name",)
    autocomplete_fields = ("owner", "parent", "edit_groups", "view_groups", "moderator")


@admin.register(PeoplePictureRelation)
class PeoplePictureRelationAdmin(admin.ModelAdmin):
    list_display = ("picture", "user")
    autocomplete_fields = ("picture", "user")


admin.site.register(Album)
