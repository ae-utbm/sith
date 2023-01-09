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

from launderette.views import *

urlpatterns = [
    # views
    path("", LaunderetteMainView.as_view(), name="launderette_main"),
    path(
        "slot/<int:slot_id>/delete/",
        SlotDeleteView.as_view(),
        name="delete_slot",
    ),
    path("book/", LaunderetteBookMainView.as_view(), name="book_main"),
    path(
        "book/<int:launderette_id>/",
        LaunderetteBookView.as_view(),
        name="book_slot",
    ),
    path(
        "<int:launderette_id>/click/",
        LaunderetteMainClickView.as_view(),
        name="main_click",
    ),
    path(
        "<int:launderette_id>/click/<int:user_id>/",
        LaunderetteClickView.as_view(),
        name="click",
    ),
    path("admin/", LaunderetteListView.as_view(), name="launderette_list"),
    path(
        "admin/<int:launderette_id>/",
        LaunderetteAdminView.as_view(),
        name="launderette_admin",
    ),
    path(
        "admin/<int:launderette_id>/edit/",
        LaunderetteEditView.as_view(),
        name="launderette_edit",
    ),
    path("admin/new/", LaunderetteCreateView.as_view(), name="launderette_new"),
    path("admin/machine/new/", MachineCreateView.as_view(), name="machine_new"),
    path(
        "admin/machine/<int:machine_id>/edit/",
        MachineEditView.as_view(),
        name="machine_edit",
    ),
    path(
        "admin/machine/<int:machine_id>/delete/",
        MachineDeleteView.as_view(),
        name="machine_delete",
    ),
]
