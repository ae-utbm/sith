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

from pedagogy.views import (
    UECommentDeleteView,
    UECommentReportCreateView,
    UECommentUpdateView,
    UECreateView,
    UEDeleteView,
    UEDetailFormView,
    UEGuideView,
    UEModerationFormView,
    UEUpdateView,
)

urlpatterns = [
    # Urls displaying the actual application for visitors
    path("", UEGuideView.as_view(), name="guide"),
    path("ue/<int:ue_id>/", UEDetailFormView.as_view(), name="ue_detail"),
    path(
        "comment/<int:comment_id>/edit/",
        UECommentUpdateView.as_view(),
        name="comment_update",
    ),
    path(
        "comment/<int:comment_id>/delete/",
        UECommentDeleteView.as_view(),
        name="comment_delete",
    ),
    path(
        "comment/<int:comment_id>/report/",
        UECommentReportCreateView.as_view(),
        name="comment_report",
    ),
    # Moderation
    path("moderation/", UEModerationFormView.as_view(), name="moderation"),
    # Administration : Create Update Delete Edit
    path("ue/create/", UECreateView.as_view(), name="ue_create"),
    path("ue/<int:ue_id>/delete/", UEDeleteView.as_view(), name="ue_delete"),
    path("ue/<int:ue_id>/edit/", UEUpdateView.as_view(), name="ue_update"),
]
