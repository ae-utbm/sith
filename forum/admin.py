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
from haystack.admin import SearchModelAdmin

from forum.models import Forum, ForumMessage, ForumTopic


@admin.register(Forum)
class ForumAdmin(SearchModelAdmin):
    search_fields = ["name", "description"]


@admin.register(ForumTopic)
class ForumTopicAdmin(SearchModelAdmin):
    search_fields = ["_title", "description"]


@admin.register(ForumMessage)
class ForumMessageAdmin(SearchModelAdmin):
    search_fields = ["title", "message"]
