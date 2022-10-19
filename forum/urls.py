# -*- coding:utf-8 -*
#
# Copyright 2016,2017,2018
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

from django.urls import path

from forum.views import *


urlpatterns = [
    path("/", ForumMainView.as_view(), name="main"),
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
