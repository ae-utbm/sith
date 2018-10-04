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

from core.views import *

urlpatterns = [
    url(r"^$", index, name="index"),
    url(r"^to_markdown$", ToMarkdownView.as_view(), name="to_markdown"),
    url(r"^notifications$", NotificationList.as_view(), name="notification_list"),
    url(r"^notification/(?P<notif_id>[0-9]+)$", notification, name="notification"),
    # Search
    url(r"^search/$", search_view, name="search"),
    url(r"^search_json/$", search_json, name="search_json"),
    url(r"^search_user/$", search_user_json, name="search_user"),
    # Login and co
    url(r"^login/$", login, name="login"),
    url(r"^logout/$", logout, name="logout"),
    url(r"^password_change/$", password_change, name="password_change"),
    url(
        r"^password_change/(?P<user_id>[0-9]+)$",
        password_root_change,
        name="password_root_change",
    ),
    url(r"^password_change/done$", password_change_done, name="password_change_done"),
    url(r"^password_reset/$", password_reset, name="password_reset"),
    url(r"^password_reset/done$", password_reset_done, name="password_reset_done"),
    url(
        r"^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$",
        password_reset_confirm,
        name="password_reset_confirm",
    ),
    url(r"^reset/done/$", password_reset_complete, name="password_reset_complete"),
    url(r"^register$", register, name="register"),
    # Group handling
    url(r"^group/$", GroupListView.as_view(), name="group_list"),
    url(r"^group/new$", GroupCreateView.as_view(), name="group_new"),
    url(r"^group/(?P<group_id>[0-9]+)/$", GroupEditView.as_view(), name="group_edit"),
    url(
        r"^group/(?P<group_id>[0-9]+)/delete$",
        GroupDeleteView.as_view(),
        name="group_delete",
    ),
    # User views
    url(r"^user/$", UserListView.as_view(), name="user_list"),
    url(
        r"^user/(?P<user_id>[0-9]+)/mini$",
        UserMiniView.as_view(),
        name="user_profile_mini",
    ),
    url(r"^user/(?P<user_id>[0-9]+)/$", UserView.as_view(), name="user_profile"),
    url(
        r"^user/(?P<user_id>[0-9]+)/pictures$",
        UserPicturesView.as_view(),
        name="user_pictures",
    ),
    url(
        r"^user/(?P<user_id>[0-9]+)/godfathers$",
        UserGodfathersView.as_view(),
        name="user_godfathers",
    ),
    url(
        r"^user/(?P<user_id>[0-9]+)/godfathers/tree$",
        UserGodfathersTreeView.as_view(),
        name="user_godfathers_tree",
    ),
    url(
        r"^user/(?P<user_id>[0-9]+)/godfathers/tree/pict$",
        UserGodfathersTreePictureView.as_view(),
        name="user_godfathers_tree_pict",
    ),
    url(
        r"^user/(?P<user_id>[0-9]+)/godfathers/(?P<godfather_id>[0-9]+)/(?P<is_father>(True)|(False))/delete$",
        DeleteUserGodfathers,
        name="user_godfathers_delete",
    ),
    url(
        r"^user/(?P<user_id>[0-9]+)/edit$",
        UserUpdateProfileView.as_view(),
        name="user_edit",
    ),
    url(
        r"^user/(?P<user_id>[0-9]+)/profile_upload$",
        UserUploadProfilePictView.as_view(),
        name="user_profile_upload",
    ),
    url(r"^user/(?P<user_id>[0-9]+)/clubs$", UserClubView.as_view(), name="user_clubs"),
    url(
        r"^user/(?P<user_id>[0-9]+)/prefs$",
        UserPreferencesView.as_view(),
        name="user_prefs",
    ),
    url(
        r"^user/(?P<user_id>[0-9]+)/groups$",
        UserUpdateGroupView.as_view(),
        name="user_groups",
    ),
    url(r"^user/tools/$", UserToolsView.as_view(), name="user_tools"),
    url(
        r"^user/(?P<user_id>[0-9]+)/account$",
        UserAccountView.as_view(),
        name="user_account",
    ),
    url(
        r"^user/(?P<user_id>[0-9]+)/account/(?P<year>[0-9]+)/(?P<month>[0-9]+)$",
        UserAccountDetailView.as_view(),
        name="user_account_detail",
    ),
    url(
        r"^user/(?P<user_id>[0-9]+)/stats$", UserStatsView.as_view(), name="user_stats"
    ),
    url(
        r"^user/(?P<user_id>[0-9]+)/gift/create$",
        GiftCreateView.as_view(),
        name="user_gift_create",
    ),
    url(
        r"^user/(?P<user_id>[0-9]+)/gift/delete/(?P<gift_id>[0-9]+)/$",
        GiftDeleteView.as_view(),
        name="user_gift_delete",
    ),
    # File views
    # url(r'^file/add/(?P<popup>popup)?$', FileCreateView.as_view(), name='file_new'),
    url(r"^file/(?P<popup>popup)?$", FileListView.as_view(), name="file_list"),
    url(
        r"^file/(?P<file_id>[0-9]+)/(?P<popup>popup)?$",
        FileView.as_view(),
        name="file_detail",
    ),
    url(
        r"^file/(?P<file_id>[0-9]+)/edit/(?P<popup>popup)?$",
        FileEditView.as_view(),
        name="file_edit",
    ),
    url(
        r"^file/(?P<file_id>[0-9]+)/prop/(?P<popup>popup)?$",
        FileEditPropView.as_view(),
        name="file_prop",
    ),
    url(
        r"^file/(?P<file_id>[0-9]+)/delete/(?P<popup>popup)?$",
        FileDeleteView.as_view(),
        name="file_delete",
    ),
    url(r"^file/moderation$", FileModerationView.as_view(), name="file_moderation"),
    url(
        r"^file/(?P<file_id>[0-9]+)/moderate$",
        FileModerateView.as_view(),
        name="file_moderate",
    ),
    url(r"^file/(?P<file_id>[0-9]+)/download$", send_file, name="download"),
    # Page views
    url(r"^page/$", PageListView.as_view(), name="page_list"),
    url(r"^page/create$", PageCreateView.as_view(), name="page_new"),
    url(
        r"^page/(?P<page_id>[0-9]*)/delete$",
        PageDeleteView.as_view(),
        name="page_delete",
    ),
    url(
        r"^page/(?P<page_name>([/a-zA-Z0-9][a-zA-Z0-9._-]*[a-zA-Z0-9])+)/edit$",
        PageEditView.as_view(),
        name="page_edit",
    ),
    url(
        r"^page/(?P<page_name>([/a-zA-Z0-9][a-zA-Z0-9._-]*[a-zA-Z0-9])+)/prop$",
        PagePropView.as_view(),
        name="page_prop",
    ),
    url(
        r"^page/(?P<page_name>([/a-zA-Z0-9][a-zA-Z0-9._-]*[a-zA-Z0-9])+)/hist$",
        PageHistView.as_view(),
        name="page_hist",
    ),
    url(
        r"^page/(?P<page_name>([/a-zA-Z0-9][a-zA-Z0-9._-]*[a-zA-Z0-9])+)/rev/(?P<rev>[0-9]+)/",
        PageRevView.as_view(),
        name="page_rev",
    ),
    url(
        r"^page/(?P<page_name>([/a-zA-Z0-9][a-zA-Z0-9._-]*[a-zA-Z0-9])+)/$",
        PageView.as_view(),
        name="page",
    ),
]
