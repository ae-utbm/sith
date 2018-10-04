# -*- coding:utf-8 -*
#
# Copyright 2017
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

from trombi.views import *

urlpatterns = [
    url(r"^(?P<club_id>[0-9]+)/new$", TrombiCreateView.as_view(), name="create"),
    url(r"^(?P<trombi_id>[0-9]+)/export$", TrombiExportView.as_view(), name="export"),
    url(r"^(?P<trombi_id>[0-9]+)/edit$", TrombiEditView.as_view(), name="edit"),
    url(
        r"^(?P<trombi_id>[0-9]+)/moderate_comments$",
        TrombiModerateCommentsView.as_view(),
        name="moderate_comments",
    ),
    url(
        r"^(?P<comment_id>[0-9]+)/moderate$",
        TrombiModerateCommentView.as_view(),
        name="moderate_comment",
    ),
    url(
        r"^user/(?P<user_id>[0-9]+)/delete$",
        TrombiDeleteUserView.as_view(),
        name="delete_user",
    ),
    url(r"^(?P<trombi_id>[0-9]+)$", TrombiDetailView.as_view(), name="detail"),
    url(
        r"^(?P<user_id>[0-9]+)/new_comment$",
        TrombiCommentCreateView.as_view(),
        name="new_comment",
    ),
    url(
        r"^(?P<user_id>[0-9]+)/profile$",
        UserTrombiProfileView.as_view(),
        name="user_profile",
    ),
    url(
        r"^comment/(?P<comment_id>[0-9]+)/edit$",
        TrombiCommentEditView.as_view(),
        name="edit_comment",
    ),
    url(r"^tools$", UserTrombiToolsView.as_view(), name="user_tools"),
    url(r"^profile$", UserTrombiEditProfileView.as_view(), name="profile"),
    url(r"^pictures$", UserTrombiEditPicturesView.as_view(), name="pictures"),
    url(
        r"^reset_memberships$",
        UserTrombiResetClubMembershipsView.as_view(),
        name="reset_memberships",
    ),
    url(
        r"^membership/(?P<membership_id>[0-9]+)/edit$",
        UserTrombiEditMembershipView.as_view(),
        name="edit_membership",
    ),
    url(
        r"^membership/(?P<membership_id>[0-9]+)/delete$",
        UserTrombiDeleteMembershipView.as_view(),
        name="delete_membership",
    ),
]
