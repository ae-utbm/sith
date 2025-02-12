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
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.models import Permission
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from core.auth.mixins import CanEditMixin
from core.models import Group, User
from core.views import DetailFormView
from core.views.forms import PermissionGroupsForm
from core.views.widgets.select import AutoCompleteSelectMultipleUser

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

    model = Group
    queryset = Group.objects.filter(is_manually_manageable=True)
    ordering = ["name"]
    template_name = "core/group_list.jinja"


class GroupEditView(CanEditMixin, UpdateView):
    """Edit infos of a Group."""

    model = Group
    queryset = Group.objects.filter(is_manually_manageable=True)
    pk_url_kwarg = "group_id"
    template_name = "core/group_edit.jinja"
    fields = ["name", "description"]


class GroupCreateView(PermissionRequiredMixin, CreateView):
    """Add a new Group."""

    model = Group
    queryset = Group.objects.filter(is_manually_manageable=True)
    template_name = "core/create.jinja"
    fields = ["name", "description"]
    permission_required = "core.add_group"


class GroupTemplateView(CanEditMixin, DetailFormView):
    """Display all users in a given Group
    Allow adding and removing users from it.
    """

    model = Group
    queryset = Group.objects.filter(is_manually_manageable=True)
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

    model = Group
    queryset = Group.objects.filter(is_manually_manageable=True)
    pk_url_kwarg = "group_id"
    template_name = "core/delete_confirm.jinja"
    success_url = reverse_lazy("core:group_list")


class PermissionGroupsUpdateView(PermissionRequiredMixin, UpdateView):
    """Manage the groups that have a specific permission.

    Notes:
        This is an `UpdateView`, but unlike typical `UpdateView`,
        it doesn't accept url arguments to retrieve the object
        to update.
        As such, a `PermissionGroupsUpdateView` can only deal with
        a single hardcoded permission.

        This is not a limitation, but an on-purpose design,
        mainly for security matters.

    Example:
        ```python
        class AddSubscriptionGroupsView(PermissionGroupsUpdateView):
            permission = "subscription.add_subscription"
            success_url = reverse_lazy("foo:bar")
        ```
    """

    permission_required = "auth.change_permission"
    template_name = "core/edit.jinja"
    form_class = PermissionGroupsForm
    permission = None

    def get_object(self, *args, **kwargs):
        if not self.permission:
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} is missing the permission attribute. "
                "Please fill it with either a permission string "
                "or a Permission object."
            )
        if isinstance(self.permission, Permission):
            return self.permission
        if isinstance(self.permission, str):
            try:
                app_label, codename = self.permission.split(".")
            except ValueError as e:
                raise ValueError(
                    "Permission name should be in the form "
                    "app_label.permission_codename."
                ) from e
            return get_object_or_404(
                Permission, codename=codename, content_type__app_label=app_label
            )
        raise TypeError(
            f"{self.__class__.__name__}.permission "
            f"must be a string or a permission instance."
        )

    def get_success_url(self):
        # if children classes define a success url, return it,
        # else stay on the same page
        return self.success_url or self.request.path
