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

"""
    This module contains views to manage Groups
"""

from django.views.generic.edit import UpdateView, CreateView, DeleteView
from django.views.generic import ListView
from django.views.generic.edit import FormView
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from django import forms

from ajax_select.fields import AutoCompleteSelectMultipleField

from core.models import RealGroup
from core.views import CanEditMixin

# Forms


class EditMembersForm(forms.Form):
    """
        Add and remove members from a Group
    """

    users_added = AutoCompleteSelectMultipleField(
        "users",
        label=_("Users to add"),
        help_text=_("Search users to add (one or more)."),
        required=False,
    )


# Views


class GroupListView(CanEditMixin, ListView):
    """
    Displays the Group list
    """

    model = RealGroup
    ordering = ["name"]
    template_name = "core/group_list.jinja"


class GroupEditView(CanEditMixin, UpdateView):
    """
        Edit infos of a Group
    """

    model = RealGroup
    pk_url_kwarg = "group_id"
    template_name = "core/group_edit.jinja"
    fields = ["name", "description"]


class GroupCreateView(CanEditMixin, CreateView):
    """
        Add a new Group
    """

    model = RealGroup
    template_name = "core/group_edit.jinja"
    fields = ["name", "description"]


class GroupTemplateView(CanEditMixin, FormView):
    """
        Display all users in a given Group
        Allow adding and removing users from it
    """

    model = RealGroup
    form_class = EditMembersForm
    pk_url_kwarg = "group_id"
    template_name = "core/group_detail.jinja"

    def get_object(self):
        """
            Get current group from id in url
        """
        return self.cached_object

    @cached_property
    def cached_object(self):
        """
            Optimisation on group retrieval
        """
        return get_object_or_404(self.model, pk=self.group_id)

    def dispatch(self, request, *args, **kwargs):

        self.group_id = kwargs[self.pk_url_kwarg]
        return super(GroupTemplateView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        data = form.clean()
        group = self.get_object()
        for user in data["users_added"]:
            group.users.add(user)
        group.save()

        return super(GroupTemplateView, self).form_valid(form)

    def get_success_url(self):
        return reverse_lazy("core:group_detail", kwargs={"group_id": self.group_id})

    def get_context_data(self):
        kwargs = super(GroupTemplateView, self).get_context_data()
        kwargs["object"] = self.get_object()
        return kwargs


class GroupDeleteView(CanEditMixin, DeleteView):
    """
        Delete a Group
    """

    model = RealGroup
    pk_url_kwarg = "group_id"
    template_name = "core/delete_confirm.jinja"
    success_url = reverse_lazy("core:group_list")
