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

from django.urls import path

from rootplace.views import (
    BanCreateView,
    BanDeleteView,
    BanView,
    DeleteAllForumUserMessagesView,
    MergeUsersView,
    OperationLogListView,
)

urlpatterns = [
    path("merge/", MergeUsersView.as_view(), name="merge"),
    path(
        "forum/messages/delete/",
        DeleteAllForumUserMessagesView.as_view(),
        name="delete_forum_messages",
    ),
    path("logs/", OperationLogListView.as_view(), name="operation_logs"),
    path("ban/", BanView.as_view(), name="ban_list"),
    path("ban/new", BanCreateView.as_view(), name="ban_create"),
    path("ban/<int:ban_id>/remove/", BanDeleteView.as_view(), name="ban_remove"),
]
