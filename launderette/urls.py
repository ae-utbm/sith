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

from django.urls import path

from launderette.views import (
    LaunderetteAdminView,
    LaunderetteBookMainView,
    LaunderetteBookView,
    LaunderetteClickView,
    LaunderetteCreateView,
    LaunderetteEditView,
    LaunderetteListView,
    LaunderetteMainClickView,
    LaunderetteMainView,
    MachineCreateView,
    MachineDeleteView,
    MachineEditView,
    SlotDeleteView,
)

urlpatterns = [
    # views
    path("", LaunderetteMainView.as_view(), name="launderette_main"),
    path("slot/<int:slot_id>/delete/", SlotDeleteView.as_view(), name="delete_slot"),
    path("book/", LaunderetteBookMainView.as_view(), name="book_main"),
    path("book/<int:launderette_id>/", LaunderetteBookView.as_view(), name="book_slot"),
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
