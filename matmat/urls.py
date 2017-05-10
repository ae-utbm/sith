# -*- coding:utf-8 -*
#
# Copyright 2017
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

from django.conf.urls import url, include

from matmat.views import *

urlpatterns = [
    url(r'^(?P<club_id>[0-9]+)/new$', MatmatCreateView.as_view(), name='create'),
    url(r'^(?P<matmat_id>[0-9]+)/edit$', MatmatEditView.as_view(), name='edit'),
    url(r'^(?P<matmat_id>[0-9]+)/delete/(?P<user_id>[0-9]+)$', MatmatDeleteUserView.as_view(), name='delete_user'),
    url(r'^(?P<matmat_id>[0-9]+)$', MatmatDetailView.as_view(), name='detail'),
    url(r'^(?P<user_id>[0-9]+)/new_comment$', MatmatCommentCreateView.as_view(), name='new_comment'),
    url(r'^comment/(?P<comment_id>[0-9]+)/edit$', MatmatCommentEditView.as_view(), name='edit_comment'),
    url(r'^tools$', UserMatmatToolsView.as_view(), name='user_tools'),
]

