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

from sas.views import *

urlpatterns = [
    path("", SASMainView.as_view(), name="main"),
    path("moderation/", ModerationView.as_view(), name="moderation"),
    path("album/<int:album_id>/", AlbumView.as_view(), name="album"),
    path(
        "album/<int:album_id>/upload/",
        AlbumUploadView.as_view(),
        name="album_upload",
    ),
    path("album/<int:album_id>/edit/", AlbumEditView.as_view(), name="album_edit"),
    path("album/<int:album_id>/preview/", send_album, name="album_preview"),
    path("picture/<int:picture_id>/", PictureView.as_view(), name="picture"),
    path(
        "picture/<int:picture_id>/edit/",
        PictureEditView.as_view(),
        name="picture_edit",
    ),
    path("picture/<int:picture_id>/download/", send_pict, name="download"),
    path(
        "picture/<int:picture_id>/download/compressed/",
        send_compressed,
        name="download_compressed",
    ),
    path(
        "picture/<int:picture_id>/download/thumb/",
        send_thumb,
        name="download_thumb",
    ),
]
