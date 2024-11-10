#
# Copyright 2023 © AE UTBM
# ae@utbm.fr / ae.info@utbm.fr
#
# This file is part of the website of the UTBM Student Association (AE UTBM),
# https://ae.utbm.fr.
#
# You can find the source code of the website at https://github.com/ae-utbm/sith
#
# LICENSED UNDER THE GNU GENERAL PUBLIC LICENSE VERSION 3 (GPLv3)
# SEE : https://raw.githubusercontent.com/ae-utbm/sith/master/LICENSE
# OR WITHIN THE LOCAL FILE "LICENSE"
#
#

"""Views to manage Groups."""

from django import forms
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from core.models import RealGroup, User
from core.views import CanCreateMixin, CanEditMixin, DetailFormView
from core.views.widgets.select import (
    AutoCompleteSelectMultipleUser,
)

# Forms


class EditMembersForm(forms.Form):
    """Add and remove members from a Group."""

    def __init__(self, *args, **kwargs):
        self.current_users = kwargs.pop("users", [])
        super().__init__(*args, **kwargs)

        self.fields["users_added"] = forms.ModelMultipleChoiceField(
            label=_("Users to add to group"),
            help_text=_("Search users to add (one or more)."),
            required=False,
            widget=AutoCompleteSelectMultipleUser,
            queryset=User.objects.exclude(id__in=self.current_users).all(),
        )

        self.fields["users_removed"] = forms.ModelMultipleChoiceField(
            User.objects.filter(id__in=self.current_users).all(),
            label=_("Users to remove from group"),
            required=False,
            widget=forms.CheckboxSelectMultiple,
        )


# Views


class GroupListView(CanEditMixin, ListView):
    """Displays the Group list."""

    model = RealGroup
    ordering = ["name"]
    template_name = "core/group_list.jinja"


class GroupEditView(CanEditMixin, UpdateView):
    """Edit infos of a Group."""

    model = RealGroup
    pk_url_kwarg = "group_id"
    template_name = "core/group_edit.jinja"
    fields = ["name", "description"]


class GroupCreateView(CanCreateMixin, CreateView):
    """Add a new Group."""

    model = RealGroup
    template_name = "core/create.jinja"
    fields = ["name", "description"]


class GroupTemplateView(CanEditMixin, DetailFormView):
    """Display all users in a given Group
    Allow adding and removing users from it.
    """

    model = RealGroup
    form_class = EditMembersForm
    pk_url_kwarg = "group_id"
    template_name = "core/group_detail.jinja"

    def form_valid(self, form):
        resp = super().form_valid(form)

        data = form.clean()
        group = self.get_object()
        if data["users_removed"]:
            for user in data["users_removed"]:
                group.users.remove(user)
        if data["users_added"]:
            for user in data["users_added"]:
                group.users.add(user)
        group.save()

        return resp

    def get_success_url(self):
        return reverse_lazy(
            "core:group_detail", kwargs={"group_id": self.get_object().id}
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["users"] = self.get_object().users.all()
        return kwargs


class GroupDeleteView(CanEditMixin, DeleteView):
    """Delete a Group."""

    model = RealGroup
    pk_url_kwarg = "group_id"
    template_name = "core/delete_confirm.jinja"
    success_url = reverse_lazy("core:group_list")
