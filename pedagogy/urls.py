#
# Copyright 2019
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

from pedagogy.views import *

urlpatterns = [
    # Urls displaying the actual application for visitors
    path("", UVGuideView.as_view(), name="guide"),
    path("uv/<int:uv_id>/", UVDetailFormView.as_view(), name="uv_detail"),
    path(
        "comment/<int:comment_id>/edit/",
        UVCommentUpdateView.as_view(),
        name="comment_update",
    ),
    path(
        "comment/<int:comment_id>/delete/",
        UVCommentDeleteView.as_view(),
        name="comment_delete",
    ),
    path(
        "comment/<int:comment_id>/report/",
        UVCommentReportCreateView.as_view(),
        name="comment_report",
    ),
    # Moderation
    path("moderation/", UVModerationFormView.as_view(), name="moderation"),
    # Administration : Create Update Delete Edit
    path("uv/create/", UVCreateView.as_view(), name="uv_create"),
    path("uv/<int:uv_id>/delete/", UVDeleteView.as_view(), name="uv_delete"),
    path("uv/<int:uv_id>/edit/", UVUpdateView.as_view(), name="uv_update"),
]
