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

from django.urls import re_path

from launderette.views import *

urlpatterns = [
    # views
    re_path(r"^$", LaunderetteMainView.as_view(), name="launderette_main"),
    re_path(
        r"^slot/(?P<slot_id>[0-9]+)/delete$",
        SlotDeleteView.as_view(),
        name="delete_slot",
    ),
    re_path(r"^book$", LaunderetteBookMainView.as_view(), name="book_main"),
    re_path(
        r"^book/(?P<launderette_id>[0-9]+)$",
        LaunderetteBookView.as_view(),
        name="book_slot",
    ),
    re_path(
        r"^(?P<launderette_id>[0-9]+)/click$",
        LaunderetteMainClickView.as_view(),
        name="main_click",
    ),
    re_path(
        r"^(?P<launderette_id>[0-9]+)/click/(?P<user_id>[0-9]+)$",
        LaunderetteClickView.as_view(),
        name="click",
    ),
    re_path(r"^admin$", LaunderetteListView.as_view(), name="launderette_list"),
    re_path(
        r"^admin/(?P<launderette_id>[0-9]+)$",
        LaunderetteAdminView.as_view(),
        name="launderette_admin",
    ),
    re_path(
        r"^admin/(?P<launderette_id>[0-9]+)/edit$",
        LaunderetteEditView.as_view(),
        name="launderette_edit",
    ),
    re_path(r"^admin/new$", LaunderetteCreateView.as_view(), name="launderette_new"),
    re_path(r"^admin/machine/new$", MachineCreateView.as_view(), name="machine_new"),
    re_path(
        r"^admin/machine/(?P<machine_id>[0-9]+)/edit$",
        MachineEditView.as_view(),
        name="machine_edit",
    ),
    re_path(
        r"^admin/machine/(?P<machine_id>[0-9]+)/delete$",
        MachineDeleteView.as_view(),
        name="machine_delete",
    ),
]
