# -*- coding:utf-8 -*
#
# Copyright 2016,2017
# - Skia <skia@libskia.so>
#
# Ce fichier fait partie du site de l'Association des Étudiants de l'UTBM,
# http://ae.utbm.fr.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License a published by the Free Software
# Foundation; either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Sofware Foundation, Inc., 59 Temple
# Place - Suite 330, Boston, MA 02111-1307, USA.
#
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
