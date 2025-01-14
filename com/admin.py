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
from django.contrib.admin import TabularInline
from haystack.admin import SearchModelAdmin

from com.models import News, NewsDate, Poster, Screen, Sith, Weekmail


class NewsDateInline(TabularInline):
    model = NewsDate
    extra = 0


@admin.register(News)
class NewsAdmin(SearchModelAdmin):
    list_display = ("title", "club", "author")
    search_fields = ("title", "summary", "content")
    autocomplete_fields = ("author", "moderator")

    inlines = [NewsDateInline]


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
