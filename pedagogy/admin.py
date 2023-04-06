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

from pedagogy.models import UV, UVComment, UVCommentReport


@admin.register(UV)
class UVAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "credit_type", "credits", "department")
    search_fields = ("code", "title", "department")
    form = make_ajax_form(UV, {"author": "users"})


@admin.register(UVComment)
class UVCommentAdmin(admin.ModelAdmin):
    list_display = ("author", "uv", "grade_global", "publish_date")
    search_fields = (
        "author__username",
        "author__first_name",
        "author__last_name",
        "uv__code",
    )
    form = make_ajax_form(UVComment, {"author": "users"})


@admin.register(UVCommentReport)
class UVCommentReportAdmin(SearchModelAdmin):
    list_display = ("reporter", "uv")
    search_fields = (
        "reporter__username",
        "reporter__first_name",
        "reporter__last_name",
        "comment__uv__code",
    )
    form = make_ajax_form(UVCommentReport, {"reporter": "users"})
