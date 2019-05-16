# -*- coding:utf-8 -*
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

from django.conf.urls import url

from pedagogy.views import *

urlpatterns = [
    url(r"^$", UVListView.as_view(), name="guide"),
    url(r"^uv/(?P<uv_id>[0-9]+)$", UVDetailFormView.as_view(), name="uv_detail"),
    url(
        r"^comment/(?P<comment_id>[0-9]+)$",
        UVCommentDetailView.as_view(),
        name="comment_detail",
    ),
    url(
        r"^comment/(?P<comment_id>[0-9]+)/report$",
        UVCommentReportCreateView.as_view(),
        name="comment_report",
    ),
    url(r"^reported$", UVCommentReportListView.as_view(), name="comment_report_list"),
    url(r"^moderation$", UVModerationFormView.as_view(), name="moderation"),
    url(r"^uv/create$", UVCreateView.as_view(), name="uv_create"),
    url(r"^uv/(?P<uv_id>[0-9]+)/delete$", UVDeleteView.as_view(), name="uv_delete"),
    url(
        r"^department/create$",
        TeachingDepartmentCreateView.as_view(),
        name="department_create",
    ),
    url(
        r"^department/(?P<department_id>[0-9]+)/delete$",
        TeachingDepartmentDeleteView.as_view(),
        name="department_delete",
    ),
    url(r"^study/create$", StudyCreateView.as_view(), name="study_create"),
    url(
        r"^study/(?P<study_id>[0-9]+)/delete$",
        StudyDeleteView.as_view(),
        name="study_delete",
    ),
]
