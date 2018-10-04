# -*- coding:utf-8 -*
#
# Copyright 2016,2017
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

from django.views.generic.edit import UpdateView, CreateView, DeleteView
from django.views.generic import ListView
from django.core.urlresolvers import reverse_lazy

from core.models import RealGroup
from core.views import CanEditMixin


class GroupListView(CanEditMixin, ListView):
    """
    Displays the group list
    """

    model = RealGroup
    template_name = "core/group_list.jinja"


class GroupEditView(CanEditMixin, UpdateView):
    model = RealGroup
    pk_url_kwarg = "group_id"
    template_name = "core/group_edit.jinja"
    fields = ["name", "description"]


class GroupCreateView(CanEditMixin, CreateView):
    model = RealGroup
    template_name = "core/group_edit.jinja"
    fields = ["name", "description"]


class GroupDeleteView(CanEditMixin, DeleteView):
    model = RealGroup
    pk_url_kwarg = "group_id"
    template_name = "core/delete_confirm.jinja"
    success_url = reverse_lazy("core:group_list")
