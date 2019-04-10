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
from django.utils.translation import ugettext_lazy as _
from django import forms

from ajax_select.fields import AutoCompleteSelectMultipleField

from core.models import RealGroup, User
from core.views import CanEditMixin, DetailFormView

# Forms


class EditMembersForm(forms.Form):
    """
        Add and remove members from a Group
    """

    def __init__(self, *args, **kwargs):
        self.current_users = kwargs.pop("users", [])
        super(EditMembersForm, self).__init__(*args, **kwargs)
        self.fields["users_removed"] = forms.ModelMultipleChoiceField(
            User.objects.filter(id__in=self.current_users).all(),
            label=_("Users to delete"),
            required=False,
            widget=forms.CheckboxSelectMultiple,
        )

    users_added = AutoCompleteSelectMultipleField(
        "users",
        label=_("Users to add"),
        help_text=_("Search users to add (one or more)."),
        required=False,
    )

    def clean_users_added(self):
        """
            Check that the user is not trying to add an user already in the group
        """
        cleaned_data = super(EditMembersForm, self).clean()
        users_added = cleaned_data.get("users_added", None)
        if not users_added:
            return users_added

        current_users = [
            str(id_) for id_ in self.current_users.values_list("id", flat=True)
        ]
        for user in users_added:
            if user in current_users:
                raise forms.ValidationError(
                    _("You can not add the same user twice"), code="invalid"
                )

        return users_added


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


class GroupTemplateView(CanEditMixin, DetailFormView):
    """
        Display all users in a given Group
        Allow adding and removing users from it
    """

    model = RealGroup
    form_class = EditMembersForm
    pk_url_kwarg = "group_id"
    template_name = "core/group_detail.jinja"

    def dispatch(self, request, *args, **kwargs):

        self.users = self.get_object().users.all()
        resp = super(GroupTemplateView, self).dispatch(request, *args, **kwargs)
        return resp

    def form_valid(self, form):
        resp = super(GroupTemplateView, self).form_valid(form)

        data = form.clean()
        group = self.get_object()
        for user in data["users_removed"]:
            group.users.remove(user)
        for user in data["users_added"]:
            group.users.add(user)
        group.save()

        return resp

    def get_success_url(self):
        return reverse_lazy(
            "core:group_detail", kwargs={"group_id": self.get_object().id}
        )

    def get_form_kwargs(self):
        kwargs = super(GroupTemplateView, self).get_form_kwargs()
        kwargs["users"] = self.users
        return kwargs


class GroupDeleteView(CanEditMixin, DeleteView):
    """
        Delete a Group
    """

    model = RealGroup
    pk_url_kwarg = "group_id"
    template_name = "core/delete_confirm.jinja"
    success_url = reverse_lazy("core:group_list")
