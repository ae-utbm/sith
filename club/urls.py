#
# Copyright 2016,2017
# - Skia <skia@libskia.so>
# - Sli <antoine@bartuccio.fr>
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

from club.views import *

urlpatterns = [
    path("", ClubListView.as_view(), name="club_list"),
    path("new/", ClubCreateView.as_view(), name="club_new"),
    path("stats/", ClubStatView.as_view(), name="club_stats"),
    path("<int:club_id>/", ClubView.as_view(), name="club_view"),
    path(
        "<int:club_id>/rev/<int:rev_id>/",
        ClubRevView.as_view(),
        name="club_view_rev",
    ),
    path("<int:club_id>/hist/", ClubPageHistView.as_view(), name="club_hist"),
    path("<int:club_id>/edit/", ClubEditView.as_view(), name="club_edit"),
    path(
        "<int:club_id>/edit/page/",
        ClubPageEditView.as_view(),
        name="club_edit_page",
    ),
    path("<int:club_id>/members/", ClubMembersView.as_view(), name="club_members"),
    path(
        "<int:club_id>/elderlies/",
        ClubOldMembersView.as_view(),
        name="club_old_members",
    ),
    path(
        "<int:club_id>/sellings/",
        ClubSellingView.as_view(),
        name="club_sellings",
    ),
    path(
        "<int:club_id>/sellings/csv/",
        ClubSellingCSVView.as_view(),
        name="sellings_csv",
    ),
    path("<int:club_id>/prop/", ClubEditPropView.as_view(), name="club_prop"),
    path("<int:club_id>/tools/", ClubToolsView.as_view(), name="tools"),
    path("<int:club_id>/mailing/", ClubMailingView.as_view(), name="mailing"),
    path(
        "<int:mailing_id>/mailing/generate/",
        MailingAutoGenerationView.as_view(),
        name="mailing_generate",
    ),
    path(
        "<int:mailing_id>/mailing/delete/",
        MailingDeleteView.as_view(),
        name="mailing_delete",
    ),
    path(
        "<int:mailing_subscription_id>/mailing/delete/subscription/",
        MailingSubscriptionDeleteView.as_view(),
        name="mailing_subscription_delete",
    ),
    path(
        "membership/<int:membership_id>/set_old/",
        MembershipSetOldView.as_view(),
        name="membership_set_old",
    ),
    path(
        "membership/<int:membership_id>/delete/",
        MembershipDeleteView.as_view(),
        name="membership_delete",
    ),
    path("<int:club_id>/poster/", PosterListView.as_view(), name="poster_list"),
    path(
        "<int:club_id>/poster/create/",
        PosterCreateView.as_view(),
        name="poster_create",
    ),
    path(
        "<int:club_id>/poster/<int:poster_id>/edit/",
        PosterEditView.as_view(),
        name="poster_edit",
    ),
    path(
        "<int:club_id>/poster/<int:poster_id>/delete/",
        PosterDeleteView.as_view(),
        name="poster_delete",
    ),
]
