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

from launderette.views import *

urlpatterns = [
    # views
    url(r"^$", LaunderetteMainView.as_view(), name="launderette_main"),
    url(
        r"^slot/(?P<slot_id>[0-9]+)/delete$",
        SlotDeleteView.as_view(),
        name="delete_slot",
    ),
    url(r"^book$", LaunderetteBookMainView.as_view(), name="book_main"),
    url(
        r"^book/(?P<launderette_id>[0-9]+)$",
        LaunderetteBookView.as_view(),
        name="book_slot",
    ),
    url(
        r"^(?P<launderette_id>[0-9]+)/click$",
        LaunderetteMainClickView.as_view(),
        name="main_click",
    ),
    url(
        r"^(?P<launderette_id>[0-9]+)/click/(?P<user_id>[0-9]+)$",
        LaunderetteClickView.as_view(),
        name="click",
    ),
    url(r"^admin$", LaunderetteListView.as_view(), name="launderette_list"),
    url(
        r"^admin/(?P<launderette_id>[0-9]+)$",
        LaunderetteAdminView.as_view(),
        name="launderette_admin",
    ),
    url(
        r"^admin/(?P<launderette_id>[0-9]+)/edit$",
        LaunderetteEditView.as_view(),
        name="launderette_edit",
    ),
    url(r"^admin/new$", LaunderetteCreateView.as_view(), name="launderette_new"),
    url(r"^admin/machine/new$", MachineCreateView.as_view(), name="machine_new"),
    url(
        r"^admin/machine/(?P<machine_id>[0-9]+)/edit$",
        MachineEditView.as_view(),
        name="machine_edit",
    ),
    url(
        r"^admin/machine/(?P<machine_id>[0-9]+)/delete$",
        MachineDeleteView.as_view(),
        name="machine_delete",
    ),
]
