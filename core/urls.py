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

from django.urls import re_path

from core.views import *

urlpatterns = [
    re_path(r"^$", index, name="index"),
    re_path(r"^to_markdown$", ToMarkdownView.as_view(), name="to_markdown"),
    re_path(r"^notifications$", NotificationList.as_view(), name="notification_list"),
    re_path(r"^notification/(?P<notif_id>[0-9]+)$", notification, name="notification"),
    # Search
    re_path(r"^search/$", search_view, name="search"),
    re_path(r"^search_json/$", search_json, name="search_json"),
    re_path(r"^search_user/$", search_user_json, name="search_user"),
    # Login and co
    re_path(r"^login/$", SithLoginView.as_view(), name="login"),
    re_path(r"^logout/$", logout, name="logout"),
    re_path(
        r"^password_change/$", SithPasswordChangeView.as_view(), name="password_change"
    ),
    re_path(
        r"^password_change/(?P<user_id>[0-9]+)$",
        password_root_change,
        name="password_root_change",
    ),
    re_path(
        r"^password_change/done$",
        SithPasswordChangeDoneView.as_view(),
        name="password_change_done",
    ),
    re_path(
        r"^password_reset/$", SithPasswordResetView.as_view(), name="password_reset"
    ),
    re_path(
        r"^password_reset/done$",
        SithPasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    re_path(
        r"^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$",
        SithPasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    re_path(
        r"^reset/done/$",
        SithPasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
    re_path(r"^register$", register, name="register"),
    # Group handling
    re_path(r"^group/$", GroupListView.as_view(), name="group_list"),
    re_path(r"^group/new$", GroupCreateView.as_view(), name="group_new"),
    re_path(
        r"^group/(?P<group_id>[0-9]+)/$", GroupEditView.as_view(), name="group_edit"
    ),
    re_path(
        r"^group/(?P<group_id>[0-9]+)/delete$",
        GroupDeleteView.as_view(),
        name="group_delete",
    ),
    re_path(
        r"^group/(?P<group_id>[0-9]+)/detail$",
        GroupTemplateView.as_view(),
        name="group_detail",
    ),
    # User views
    re_path(r"^user/$", UserListView.as_view(), name="user_list"),
    re_path(
        r"^user/(?P<user_id>[0-9]+)/mini$",
        UserMiniView.as_view(),
        name="user_profile_mini",
    ),
    re_path(r"^user/(?P<user_id>[0-9]+)/$", UserView.as_view(), name="user_profile"),
    re_path(
        r"^user/(?P<user_id>[0-9]+)/pictures$",
        UserPicturesView.as_view(),
        name="user_pictures",
    ),
    re_path(
        r"^user/(?P<user_id>[0-9]+)/godfathers$",
        UserGodfathersView.as_view(),
        name="user_godfathers",
    ),
    re_path(
        r"^user/(?P<user_id>[0-9]+)/godfathers/tree$",
        UserGodfathersTreeView.as_view(),
        name="user_godfathers_tree",
    ),
    re_path(
        r"^user/(?P<user_id>[0-9]+)/godfathers/tree/pict$",
        UserGodfathersTreePictureView.as_view(),
        name="user_godfathers_tree_pict",
    ),
    re_path(
        r"^user/(?P<user_id>[0-9]+)/godfathers/(?P<godfather_id>[0-9]+)/(?P<is_father>(True)|(False))/delete$",
        DeleteUserGodfathers,
        name="user_godfathers_delete",
    ),
    re_path(
        r"^user/(?P<user_id>[0-9]+)/edit$",
        UserUpdateProfileView.as_view(),
        name="user_edit",
    ),
    re_path(
        r"^user/(?P<user_id>[0-9]+)/profile_upload$",
        UserUploadProfilePictView.as_view(),
        name="user_profile_upload",
    ),
    re_path(
        r"^user/(?P<user_id>[0-9]+)/clubs$", UserClubView.as_view(), name="user_clubs"
    ),
    re_path(
        r"^user/(?P<user_id>[0-9]+)/prefs$",
        UserPreferencesView.as_view(),
        name="user_prefs",
    ),
    re_path(
        r"^user/(?P<user_id>[0-9]+)/groups$",
        UserUpdateGroupView.as_view(),
        name="user_groups",
    ),
    re_path(r"^user/tools/$", UserToolsView.as_view(), name="user_tools"),
    re_path(
        r"^user/(?P<user_id>[0-9]+)/account$",
        UserAccountView.as_view(),
        name="user_account",
    ),
    re_path(
        r"^user/(?P<user_id>[0-9]+)/account/(?P<year>[0-9]+)/(?P<month>[0-9]+)$",
        UserAccountDetailView.as_view(),
        name="user_account_detail",
    ),
    re_path(
        r"^user/(?P<user_id>[0-9]+)/stats$", UserStatsView.as_view(), name="user_stats"
    ),
    re_path(
        r"^user/(?P<user_id>[0-9]+)/gift/create$",
        GiftCreateView.as_view(),
        name="user_gift_create",
    ),
    re_path(
        r"^user/(?P<user_id>[0-9]+)/gift/delete/(?P<gift_id>[0-9]+)/$",
        GiftDeleteView.as_view(),
        name="user_gift_delete",
    ),
    # File views
    # re_path(r'^file/add/(?P<popup>popup)?$', FileCreateView.as_view(), name='file_new'),
    re_path(r"^file/(?P<popup>popup)?$", FileListView.as_view(), name="file_list"),
    re_path(
        r"^file/(?P<file_id>[0-9]+)/(?P<popup>popup)?$",
        FileView.as_view(),
        name="file_detail",
    ),
    re_path(
        r"^file/(?P<file_id>[0-9]+)/edit/(?P<popup>popup)?$",
        FileEditView.as_view(),
        name="file_edit",
    ),
    re_path(
        r"^file/(?P<file_id>[0-9]+)/prop/(?P<popup>popup)?$",
        FileEditPropView.as_view(),
        name="file_prop",
    ),
    re_path(
        r"^file/(?P<file_id>[0-9]+)/delete/(?P<popup>popup)?$",
        FileDeleteView.as_view(),
        name="file_delete",
    ),
    re_path(r"^file/moderation$", FileModerationView.as_view(), name="file_moderation"),
    re_path(
        r"^file/(?P<file_id>[0-9]+)/moderate$",
        FileModerateView.as_view(),
        name="file_moderate",
    ),
    re_path(r"^file/(?P<file_id>[0-9]+)/download$", send_file, name="download"),
    # Page views
    re_path(r"^page/$", PageListView.as_view(), name="page_list"),
    re_path(r"^page/create$", PageCreateView.as_view(), name="page_new"),
    re_path(
        r"^page/(?P<page_id>[0-9]*)/delete$",
        PageDeleteView.as_view(),
        name="page_delete",
    ),
    re_path(
        r"^page/(?P<page_name>([/a-zA-Z0-9][a-zA-Z0-9._-]*[a-zA-Z0-9])+)/edit$",
        PageEditView.as_view(),
        name="page_edit",
    ),
    re_path(
        r"^page/(?P<page_name>([/a-zA-Z0-9][a-zA-Z0-9._-]*[a-zA-Z0-9])+)/prop$",
        PagePropView.as_view(),
        name="page_prop",
    ),
    re_path(
        r"^page/(?P<page_name>([/a-zA-Z0-9][a-zA-Z0-9._-]*[a-zA-Z0-9])+)/hist$",
        PageHistView.as_view(),
        name="page_hist",
    ),
    re_path(
        r"^page/(?P<page_name>([/a-zA-Z0-9][a-zA-Z0-9._-]*[a-zA-Z0-9])+)/rev/(?P<rev>[0-9]+)/",
        PageRevView.as_view(),
        name="page_rev",
    ),
    re_path(
        r"^page/(?P<page_name>([/a-zA-Z0-9][a-zA-Z0-9._-]*[a-zA-Z0-9])+)/$",
        PageView.as_view(),
        name="page",
    ),
]
