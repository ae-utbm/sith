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
from haystack.admin import SearchModelAdmin

from com.models import *


@admin.register(News)
class NewsAdmin(SearchModelAdmin):
    list_display = ("title", "type", "club", "author")
    search_fields = ("title", "summary", "content")
    autocomplete_fields = ("author", "moderator")


@admin.register(Poster)
class PosterAdmin(SearchModelAdmin):
    list_display = ("name", "club", "date_begin", "date_end", "moderator")
    autocomplete_fields = ("moderator",)


@admin.register(Weekmail)
class WeekmailAdmin(SearchModelAdmin):
    list_display = ("title", "sent")
    search_fields = ("title",)


admin.site.register(Sith)
admin.site.register(Screen)
