# -*- coding:utf-8 -*
#
# Copyright 2017,2020
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

from trombi.views import *

urlpatterns = [
    path("<int:club_id>/new/", TrombiCreateView.as_view(), name="create"),
    path("<int:trombi_id>/export/", TrombiExportView.as_view(), name="export"),
    path("<int:trombi_id>/edit/", TrombiEditView.as_view(), name="edit"),
    path(
        "<int:trombi_id>/moderate_comments/",
        TrombiModerateCommentsView.as_view(),
        name="moderate_comments",
    ),
    path(
        "<int:comment_id>/moderate/",
        TrombiModerateCommentView.as_view(),
        name="moderate_comment",
    ),
    path(
        "user/<int:user_id>/delete/",
        TrombiDeleteUserView.as_view(),
        name="delete_user",
    ),
    path("<int:trombi_id>/", TrombiDetailView.as_view(), name="detail"),
    path(
        "<int:user_id>/new_comment/",
        TrombiCommentCreateView.as_view(),
        name="new_comment",
    ),
    path(
        "<int:user_id>/profile/",
        UserTrombiProfileView.as_view(),
        name="user_profile",
    ),
    path(
        "comment/<int:comment_id>/edit/",
        TrombiCommentEditView.as_view(),
        name="edit_comment",
    ),
    path("tools/", UserTrombiToolsView.as_view(), name="user_tools"),
    path("profile/", UserTrombiEditProfileView.as_view(), name="profile"),
    path("pictures/", UserTrombiEditPicturesView.as_view(), name="pictures"),
    path(
        "reset_memberships/",
        UserTrombiResetClubMembershipsView.as_view(),
        name="reset_memberships",
    ),
    path(
        "membership/<int:membership_id>/edit/",
        UserTrombiEditMembershipView.as_view(),
        name="edit_membership",
    ),
    path(
        "membership/<int:membership_id>/delete/",
        UserTrombiDeleteMembershipView.as_view(),
        name="delete_membership",
    ),
    path(
        "membership/<int:user_id>/create/",
        UserTrombiAddMembershipView.as_view(),
        name="create_membership",
    ),
]
