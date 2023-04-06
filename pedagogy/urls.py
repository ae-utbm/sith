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

from django.urls import path

from pedagogy.views import *

urlpatterns = [
    # Urls displaying the actual application for visitors
    path("", UVListView.as_view(), name="guide"),
    path("uv/<int:uv_id>/", UVDetailFormView.as_view(), name="uv_detail"),
    path(
        "comment/<int:comment_id>/edit/",
        UVCommentUpdateView.as_view(),
        name="comment_update",
    ),
    path(
        "comment/<int:comment_id>/delete/",
        UVCommentDeleteView.as_view(),
        name="comment_delete",
    ),
    path(
        "comment/<int:comment_id>/report/",
        UVCommentReportCreateView.as_view(),
        name="comment_report",
    ),
    # Moderation
    path("moderation/", UVModerationFormView.as_view(), name="moderation"),
    # Administration : Create Update Delete Edit
    path("uv/create/", UVCreateView.as_view(), name="uv_create"),
    path("uv/<int:uv_id>/delete/", UVDeleteView.as_view(), name="uv_delete"),
    path("uv/<int:uv_id>/edit/", UVUpdateView.as_view(), name="uv_update"),
]
