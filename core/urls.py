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

from django.urls import path, re_path, register_converter

from core.converters import (
    BooleanStringConverter,
    FourDigitYearConverter,
    TwoDigitMonthConverter,
)
from core.views import *

register_converter(FourDigitYearConverter, "yyyy")
register_converter(TwoDigitMonthConverter, "mm")
register_converter(BooleanStringConverter, "bool")


urlpatterns = [
    path("", index, name="index"),
    path("to_markdown/", ToMarkdownView.as_view(), name="to_markdown"),
    path("notifications/", NotificationList.as_view(), name="notification_list"),
    path("notification/<int:notif_id>/", notification, name="notification"),
    # Search
    path("search/", search_view, name="search"),
    path("search_json/", search_json, name="search_json"),
    path("search_user/", search_user_json, name="search_user"),
    # Login and co
    path("login/", SithLoginView.as_view(), name="login"),
    path("logout/", logout, name="logout"),
    path("password_change/", SithPasswordChangeView.as_view(), name="password_change"),
    path(
        "password_change/<int:user_id>/",
        password_root_change,
        name="password_root_change",
    ),
    path(
        "password_change/done/",
        SithPasswordChangeDoneView.as_view(),
        name="password_change_done",
    ),
    path("password_reset/", SithPasswordResetView.as_view(), name="password_reset"),
    path(
        "password_reset/done/",
        SithPasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        r"reset/<str:uidb64>/<str:token>/",
        SithPasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        SithPasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
    path("register/", register, name="register"),
    # Group handling
    path("group/", GroupListView.as_view(), name="group_list"),
    path("group/new/", GroupCreateView.as_view(), name="group_new"),
    path("group/<int:group_id>/", GroupEditView.as_view(), name="group_edit"),
    path(
        "group/<int:group_id>/delete/",
        GroupDeleteView.as_view(),
        name="group_delete",
    ),
    path(
        "group/<int:group_id>/detail/",
        GroupTemplateView.as_view(),
        name="group_detail",
    ),
    # User views
    path("user/", UserListView.as_view(), name="user_list"),
    path(
        "user/<int:user_id>/mini/",
        UserMiniView.as_view(),
        name="user_profile_mini",
    ),
    path("user/<int:user_id>/", UserView.as_view(), name="user_profile"),
    path(
        "user/<int:user_id>/pictures/",
        UserPicturesView.as_view(),
        name="user_pictures",
    ),
    path(
        "user/<int:user_id>/godfathers/",
        UserGodfathersView.as_view(),
        name="user_godfathers",
    ),
    path(
        "user/<int:user_id>/godfathers/tree/",
        UserGodfathersTreeView.as_view(),
        name="user_godfathers_tree",
    ),
    path(
        "user/<int:user_id>/godfathers/tree/pict/",
        UserGodfathersTreePictureView.as_view(),
        name="user_godfathers_tree_pict",
    ),
    path(
        "user/<int:user_id>/godfathers/<int:godfather_id>/<bool:is_father>/delete/",
        delete_user_godfather,
        name="user_godfathers_delete",
    ),
    path(
        "user/<int:user_id>/edit/",
        UserUpdateProfileView.as_view(),
        name="user_edit",
    ),
    path(
        "user/<int:user_id>/profile_upload/",
        UserUploadProfilePictView.as_view(),
        name="user_profile_upload",
    ),
    path("user/<int:user_id>/clubs/", UserClubView.as_view(), name="user_clubs"),
    path(
        "user/<int:user_id>/prefs/",
        UserPreferencesView.as_view(),
        name="user_prefs",
    ),
    path(
        "user/<int:user_id>/groups/",
        UserUpdateGroupView.as_view(),
        name="user_groups",
    ),
    path("user/tools/", UserToolsView.as_view(), name="user_tools"),
    path(
        "user/<int:user_id>/account/",
        UserAccountView.as_view(),
        name="user_account",
    ),
    path(
        "user/<int:user_id>/account/<yyyy:year>/<mm:month>/",
        UserAccountDetailView.as_view(),
        name="user_account_detail",
    ),
    path("user/<int:user_id>/stats/", UserStatsView.as_view(), name="user_stats"),
    path(
        "user/<int:user_id>/gift/create/",
        GiftCreateView.as_view(),
        name="user_gift_create",
    ),
    path(
        "user/<int:user_id>/gift/delete/<int:gift_id>/",
        GiftDeleteView.as_view(),
        name="user_gift_delete",
    ),
    # File views
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
    path("file/moderation/", FileModerationView.as_view(), name="file_moderation"),
    path(
        "file/<int:file_id>/moderate/",
        FileModerateView.as_view(),
        name="file_moderate",
    ),
    path("file/<int:file_id>/download/", send_file, name="download"),
    # Page views
    path("page/", PageListView.as_view(), name="page_list"),
    path("page/create/", PageCreateView.as_view(), name="page_new"),
    path(
        "page/<int:page_id>/delete/",
        PageDeleteView.as_view(),
        name="page_delete",
    ),
    path(
        "page/<path:page_name>/edit/",
        PageEditView.as_view(),
        name="page_edit",
    ),
    path(
        "page/<path:page_name>/prop/",
        PagePropView.as_view(),
        name="page_prop",
    ),
    path(
        "page/<path:page_name>/hist/",
        PageHistView.as_view(),
        name="page_hist",
    ),
    path(
        "page/<path:page_name>/rev/<int:rev>/",
        PageRevView.as_view(),
        name="page_rev",
    ),
    path(
        "page/<path:page_name>/",
        PageView.as_view(),
        name="page",
    ),
]
