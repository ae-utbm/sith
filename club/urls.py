# -*- coding:utf-8 -*
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

from django.conf.urls import url

from club.views import *

urlpatterns = [
    url(r"^$", ClubListView.as_view(), name="club_list"),
    url(r"^new$", ClubCreateView.as_view(), name="club_new"),
    url(r"^stats$", ClubStatView.as_view(), name="club_stats"),
    url(r"^(?P<club_id>[0-9]+)/$", ClubView.as_view(), name="club_view"),
    url(
        r"^(?P<club_id>[0-9]+)/rev/(?P<rev_id>[0-9]+)/$",
        ClubRevView.as_view(),
        name="club_view_rev",
    ),
    url(r"^(?P<club_id>[0-9]+)/hist$", ClubPageHistView.as_view(), name="club_hist"),
    url(r"^(?P<club_id>[0-9]+)/edit$", ClubEditView.as_view(), name="club_edit"),
    url(
        r"^(?P<club_id>[0-9]+)/edit/page$",
        ClubPageEditView.as_view(),
        name="club_edit_page",
    ),
    url(
        r"^(?P<club_id>[0-9]+)/members$", ClubMembersView.as_view(), name="club_members"
    ),
    url(
        r"^(?P<club_id>[0-9]+)/elderlies$",
        ClubOldMembersView.as_view(),
        name="club_old_members",
    ),
    url(
        r"^(?P<club_id>[0-9]+)/sellings$",
        ClubSellingView.as_view(),
        name="club_sellings",
    ),
    url(
        r"^(?P<club_id>[0-9]+)/sellings/csv$",
        ClubSellingCSVView.as_view(),
        name="sellings_csv",
    ),
    url(r"^(?P<club_id>[0-9]+)/prop$", ClubEditPropView.as_view(), name="club_prop"),
    url(r"^(?P<club_id>[0-9]+)/tools$", ClubToolsView.as_view(), name="tools"),
    url(
        r"^(?P<club_id>[0-9]+)/mailing$",
        ClubMailingView.as_view(action="display"),
        name="mailing",
    ),
    url(
        r"^(?P<club_id>[0-9]+)/mailing/new/mailing$",
        ClubMailingView.as_view(action="add_mailing"),
        name="mailing_create",
    ),
    url(
        r"^(?P<club_id>[0-9]+)/mailing/new/subscription$",
        ClubMailingView.as_view(action="add_member"),
        name="mailing_subscription_create",
    ),
    url(
        r"^(?P<mailing_id>[0-9]+)/mailing/generate$",
        MailingAutoGenerationView.as_view(),
        name="mailing_generate",
    ),
    url(
        r"^(?P<mailing_id>[0-9]+)/mailing/clean$",
        MailingAutoCleanView.as_view(),
        name="mailing_clean",
    ),
    url(
        r"^(?P<mailing_id>[0-9]+)/mailing/delete$",
        MailingDeleteView.as_view(),
        name="mailing_delete",
    ),
    url(
        r"^(?P<mailing_subscription_id>[0-9]+)/mailing/delete/subscription$",
        MailingSubscriptionDeleteView.as_view(),
        name="mailing_subscription_delete",
    ),
    url(
        r"^membership/(?P<membership_id>[0-9]+)/set_old$",
        MembershipSetOldView.as_view(),
        name="membership_set_old",
    ),
    url(r"^(?P<club_id>[0-9]+)/poster$", PosterListView.as_view(), name="poster_list"),
    url(
        r"^(?P<club_id>[0-9]+)/poster/create$",
        PosterCreateView.as_view(),
        name="poster_create",
    ),
    url(
        r"^(?P<club_id>[0-9]+)/poster/(?P<poster_id>[0-9]+)/edit$",
        PosterEditView.as_view(),
        name="poster_edit",
    ),
    url(
        r"^(?P<club_id>[0-9]+)/poster/(?P<poster_id>[0-9]+)/delete$",
        PosterDeleteView.as_view(),
        name="poster_delete",
    ),
]
