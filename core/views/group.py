# -*- coding:utf-8 -*-
#
# Copyright 2023 © AE UTBM
# ae@utbm.fr / ae.info@utbm.fr
# All contributors are listed in the CONTRIBUTORS file.
#
# This file is part of the website of the UTBM Student Association (AE UTBM),
# https://ae.utbm.fr.
#
# You can find the whole source code at https://github.com/ae-utbm/sith3
#
# LICENSED UNDER THE GNU GENERAL PUBLIC LICENSE VERSION 3 (GPLv3)
# SEE : https://raw.githubusercontent.com/ae-utbm/sith3/master/LICENSE
# OR WITHIN THE LOCAL FILE "LICENSE"
#
# PREVIOUSLY LICENSED UNDER THE MIT LICENSE,
# SEE : https://raw.githubusercontent.com/ae-utbm/sith3/master/LICENSE.old
# OR WITHIN THE LOCAL FILE "LICENSE.old"
#

"""
This module contains views to manage Groups
"""

from ajax_select.fields import AutoCompleteSelectMultipleField
from django import forms
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from core.models import RealGroup, User
from core.views import CanCreateMixin, CanEditMixin, DetailFormView

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
            label=_("Users to remove from group"),
            required=False,
            widget=forms.CheckboxSelectMultiple,
        )

    users_added = AutoCompleteSelectMultipleField(
        "users",
        label=_("Users to add to group"),
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


class GroupCreateView(CanCreateMixin, CreateView):
    """
    Add a new Group
    """

    model = RealGroup
    template_name = "core/create.jinja"
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
        kwargs["users"] = self.get_object().users.all()
        return kwargs


class GroupDeleteView(CanEditMixin, DeleteView):
    """
    Delete a Group
    """

    model = RealGroup
    pk_url_kwarg = "group_id"
    template_name = "core/delete_confirm.jinja"
    success_url = reverse_lazy("core:group_list")
