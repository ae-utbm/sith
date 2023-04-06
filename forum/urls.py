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

from forum.views import *

urlpatterns = [
    path("", ForumMainView.as_view(), name="main"),
    path("search/", ForumSearchView.as_view(), name="search"),
    path("new_forum/", ForumCreateView.as_view(), name="new_forum"),
    path("mark_all_as_read/", ForumMarkAllAsRead.as_view(), name="mark_all_as_read"),
    path("last_unread/", ForumLastUnread.as_view(), name="last_unread"),
    path("favorite_topics/", ForumFavoriteTopics.as_view(), name="favorite_topics"),
    path("<int:forum_id>/", ForumDetailView.as_view(), name="view_forum"),
    path("<int:forum_id>/edit/", ForumEditView.as_view(), name="edit_forum"),
    path("<int:forum_id>/delete/", ForumDeleteView.as_view(), name="delete_forum"),
    path(
        "<int:forum_id>/new_topic/",
        ForumTopicCreateView.as_view(),
        name="new_topic",
    ),
    path(
        "topic/<int:topic_id>/",
        ForumTopicDetailView.as_view(),
        name="view_topic",
    ),
    path(
        "topic/<int:topic_id>/edit/",
        ForumTopicEditView.as_view(),
        name="edit_topic",
    ),
    path(
        "topic/<int:topic_id>/new_message/",
        ForumMessageCreateView.as_view(),
        name="new_message",
    ),
    path(
        "topic/<int:topic_id>/toggle_subscribe/",
        ForumTopicSubscribeView.as_view(),
        name="toggle_subscribe_topic",
    ),
    path(
        "message/<int:message_id>/",
        ForumMessageView.as_view(),
        name="view_message",
    ),
    path(
        "message/<int:message_id>/edit/",
        ForumMessageEditView.as_view(),
        name="edit_message",
    ),
    path(
        "message/<int:message_id>/delete/",
        ForumMessageDeleteView.as_view(),
        name="delete_message",
    ),
    path(
        "message/<int:message_id>/undelete/",
        ForumMessageUndeleteView.as_view(),
        name="undelete_message",
    ),
]
