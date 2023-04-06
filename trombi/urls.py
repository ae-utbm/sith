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
