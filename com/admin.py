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
from haystack.admin import SearchModelAdmin

from com.models import *


@admin.register(News)
class NewsAdmin(SearchModelAdmin):
    list_display = ("title", "type", "club", "author")
    search_fields = ("title", "summary", "content")
    form = make_ajax_form(
        News,
        {
            "author": "users",
            "moderator": "users",
        },
    )


@admin.register(Poster)
class PosterAdmin(SearchModelAdmin):
    list_display = ("name", "club", "date_begin", "date_end", "moderator")
    form = make_ajax_form(Poster, {"moderator": "users"})


@admin.register(Weekmail)
class WeekmailAdmin(SearchModelAdmin):
    list_display = ("title", "sent")
    search_fields = ("title",)


admin.site.register(Sith)
admin.site.register(Screen)
