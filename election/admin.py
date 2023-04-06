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

from election.models import Candidature, Election, ElectionList, Role


@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "is_candidature_active",
        "is_vote_active",
        "is_vote_finished",
        "archived",
    )
    form = make_ajax_form(Election, {"voters": "users"})


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("election", "title", "max_choice")
    search_fields = ("election__title", "title")


@admin.register(ElectionList)
class ElectionListAdmin(admin.ModelAdmin):
    list_display = ("election", "title")
    search_fields = ("election__title", "title")


@admin.register(Candidature)
class CandidatureAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "election_list")
    form = make_ajax_form(Candidature, {"user": "users"})


# Votes must stay fully anonymous, so no ModelAdmin for Vote model
