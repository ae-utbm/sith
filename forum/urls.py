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

from django.conf.urls import url

from forum.views import *

urlpatterns = [
    url(r"^$", ForumMainView.as_view(), name="main"),
    url(r"^new_forum$", ForumCreateView.as_view(), name="new_forum"),
    url(r"^mark_all_as_read$", ForumMarkAllAsRead.as_view(), name="mark_all_as_read"),
    url(r"^last_unread$", ForumLastUnread.as_view(), name="last_unread"),
    url(r"^favorite_topics$", ForumFavoriteTopics.as_view(), name="favorite_topics"),
    url(r"^(?P<forum_id>[0-9]+)$", ForumDetailView.as_view(), name="view_forum"),
    url(r"^(?P<forum_id>[0-9]+)/edit$", ForumEditView.as_view(), name="edit_forum"),
    url(
        r"^(?P<forum_id>[0-9]+)/delete$", ForumDeleteView.as_view(), name="delete_forum"
    ),
    url(
        r"^(?P<forum_id>[0-9]+)/new_topic$",
        ForumTopicCreateView.as_view(),
        name="new_topic",
    ),
    url(
        r"^topic/(?P<topic_id>[0-9]+)$",
        ForumTopicDetailView.as_view(),
        name="view_topic",
    ),
    url(
        r"^topic/(?P<topic_id>[0-9]+)/edit$",
        ForumTopicEditView.as_view(),
        name="edit_topic",
    ),
    url(
        r"^topic/(?P<topic_id>[0-9]+)/new_message$",
        ForumMessageCreateView.as_view(),
        name="new_message",
    ),
    url(
        r"^topic/(?P<topic_id>[0-9]+)/toggle_subscribe$",
        ForumTopicSubscribeView.as_view(),
        name="toggle_subscribe_topic",
    ),
    url(
        r"^message/(?P<message_id>[0-9]+)$",
        ForumMessageView.as_view(),
        name="view_message",
    ),
    url(
        r"^message/(?P<message_id>[0-9]+)/edit$",
        ForumMessageEditView.as_view(),
        name="edit_message",
    ),
    url(
        r"^message/(?P<message_id>[0-9]+)/delete$",
        ForumMessageDeleteView.as_view(),
        name="delete_message",
    ),
    url(
        r"^message/(?P<message_id>[0-9]+)/undelete$",
        ForumMessageUndeleteView.as_view(),
        name="undelete_message",
    ),
]
