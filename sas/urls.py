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

from django.conf.urls import url

from sas.views import *

urlpatterns = [
    url(r"^$", SASMainView.as_view(), name="main"),
    url(r"^moderation$", ModerationView.as_view(), name="moderation"),
    url(r"^album/(?P<album_id>[0-9]+)$", AlbumView.as_view(), name="album"),
    url(
        r"^album/(?P<album_id>[0-9]+)/upload$",
        AlbumUploadView.as_view(),
        name="album_upload",
    ),
    url(
        r"^album/(?P<album_id>[0-9]+)/edit$", AlbumEditView.as_view(), name="album_edit"
    ),
    url(r"^album/(?P<album_id>[0-9]+)/preview$", send_album, name="album_preview"),
    url(r"^picture/(?P<picture_id>[0-9]+)$", PictureView.as_view(), name="picture"),
    url(
        r"^picture/(?P<picture_id>[0-9]+)/edit$",
        PictureEditView.as_view(),
        name="picture_edit",
    ),
    url(r"^picture/(?P<picture_id>[0-9]+)/download$", send_pict, name="download"),
    url(
        r"^picture/(?P<picture_id>[0-9]+)/download/compressed$",
        send_compressed,
        name="download_compressed",
    ),
    url(
        r"^picture/(?P<picture_id>[0-9]+)/download/thumb$",
        send_thumb,
        name="download_thumb",
    ),
    # url(r'^album/new$', AlbumCreateView.as_view(), name='album_new'),
    # url(r'^(?P<club_id>[0-9]+)/$', ClubView.as_view(), name='club_view'),
]
