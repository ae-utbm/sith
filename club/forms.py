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

from ajax_select.fields import AutoCompleteSelectMultipleField
from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from club.models import Club, Mailing, MailingSubscription, Membership
from core.models import User
from core.views.forms import SelectDate, TzAwareDateTimeField
from counter.models import Counter


class ClubEditForm(forms.ModelForm):
    class Meta:
        model = Club
        fields = ["address", "logo", "short_description"]

    def __init__(self, *args, **kwargs):
        super(ClubEditForm, self).__init__(*args, **kwargs)
        self.fields["short_description"].widget = forms.Textarea()


class MailingForm(forms.Form):
    """
    Form handling mailing lists right
    """

    ACTION_NEW_MAILING = 1
    ACTION_NEW_SUBSCRIPTION = 2
    ACTION_REMOVE_SUBSCRIPTION = 3

    subscription_users = AutoCompleteSelectMultipleField(
        "users",
        label=_("Users to add"),
        help_text=_("Search users to add (one or more)."),
        required=False,
    )

    def __init__(self, club_id, user_id, mailings, *args, **kwargs):
        super(MailingForm, self).__init__(*args, **kwargs)

        self.fields["action"] = forms.TypedChoiceField(
            choices=(
                (self.ACTION_NEW_MAILING, _("New Mailing")),
                (self.ACTION_NEW_SUBSCRIPTION, _("Subscribe")),
                (self.ACTION_REMOVE_SUBSCRIPTION, _("Remove")),
            ),
            coerce=int,
            label=_("Action"),
            initial=1,
            required=True,
            widget=forms.HiddenInput(),
        )

        # Generate bulk removal forms, they are never required
        for mailing in mailings:
            self.fields["removal_" + str(mailing.id)] = forms.ModelMultipleChoiceField(
                mailing.subscriptions.all(),
                label=_("Remove"),
                required=False,
                widget=forms.CheckboxSelectMultiple,
            )

        # Include fields for handling mailing creation
        mailing_fields = ("email",)
        self.fields.update(forms.fields_for_model(Mailing, fields=mailing_fields))
        for field in mailing_fields:
            self.fields["mailing_" + field] = self.fields.pop(field)
            self.fields["mailing_" + field].required = False

        # Include fields for handling subscription creation
        subscription_fields = ("mailing", "email")
        self.fields.update(
            forms.fields_for_model(MailingSubscription, fields=subscription_fields)
        )
        for field in subscription_fields:
            self.fields["subscription_" + field] = self.fields.pop(field)
            self.fields["subscription_" + field].required = False

        self.fields["subscription_mailing"].queryset = Mailing.objects.filter(
            club__id=club_id, is_moderated=True
        )

    def check_required(self, cleaned_data, field):
        """
        If the given field doesn't exist or has no value, add a required error on it
        """
        if not cleaned_data.get(field, None):
            self.add_error(field, _("This field is required"))

    def clean_subscription_users(self):
        """
        Convert given users into real users and check their validity
        """
        cleaned_data = super(MailingForm, self).clean()
        users = []
        for user in cleaned_data["subscription_users"]:
            user = User.objects.filter(id=user).first()
            if not user:
                raise forms.ValidationError(
                    _("One of the selected users doesn't exist"), code="invalid"
                )
            if not user.email:
                raise forms.ValidationError(
                    _("One of the selected users doesn't have an email address"),
                    code="invalid",
                )
            users.append(user)
        return users

    def clean(self):
        cleaned_data = super(MailingForm, self).clean()

        if not "action" in cleaned_data:
            # If there is no action provided, we can stop here
            raise forms.ValidationError(_("An action is required"), code="invalid")

        if cleaned_data["action"] == self.ACTION_NEW_MAILING:
            self.check_required(cleaned_data, "mailing_email")

        if cleaned_data["action"] == self.ACTION_NEW_SUBSCRIPTION:
            self.check_required(cleaned_data, "subscription_mailing")
            if not cleaned_data.get(
                "subscription_users", None
            ) and not cleaned_data.get("subscription_email", None):
                raise forms.ValidationError(
                    _("You must specify at least an user or an email address"),
                    code="invalid",
                )

        return cleaned_data


class SellingsForm(forms.Form):
    begin_date = TzAwareDateTimeField(label=_("Begin date"), required=False)
    end_date = TzAwareDateTimeField(label=_("End date"), required=False)

    counters = forms.ModelMultipleChoiceField(
        Counter.objects.order_by("name").all(), label=_("Counter"), required=False
    )

    def __init__(self, club, *args, **kwargs):
        super(SellingsForm, self).__init__(*args, **kwargs)
        self.fields["products"] = forms.ModelMultipleChoiceField(
            club.products.order_by("name").filter(archived=False).all(),
            label=_("Products"),
            required=False,
        )
        self.fields["archived_products"] = forms.ModelMultipleChoiceField(
            club.products.order_by("name").filter(archived=True).all(),
            label=_("Archived products"),
            required=False,
        )


class ClubMemberForm(forms.Form):
    """
    Form handling the members of a club
    """

    error_css_class = "error"
    required_css_class = "required"

    users = AutoCompleteSelectMultipleField(
        "users",
        label=_("Users to add"),
        help_text=_("Search users to add (one or more)."),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        self.club = kwargs.pop("club")
        self.request_user = kwargs.pop("request_user")
        self.club_members = kwargs.pop("club_members", None)
        if not self.club_members:
            self.club_members = (
                self.club.members.filter(end_date=None).order_by("-role").all()
            )
        self.request_user_membership = self.club.get_membership_for(self.request_user)
        super(ClubMemberForm, self).__init__(*args, **kwargs)

        # Using a ModelForm binds too much the form with the model and we don't want that
        # We want the view to process the model creation since they are multiple users
        # We also want the form to handle bulk deletion
        self.fields.update(
            forms.fields_for_model(
                Membership,
                fields=("role", "start_date", "description"),
                widgets={"start_date": SelectDate},
            )
        )

        # Role is required only if users is specified
        self.fields["role"].required = False

        # Start date and description are never really required
        self.fields["start_date"].required = False
        self.fields["description"].required = False

        self.fields["users_old"] = forms.ModelMultipleChoiceField(
            User.objects.filter(
                id__in=[
                    ms.user.id
                    for ms in self.club_members
                    if ms.can_be_edited_by(self.request_user)
                ]
            ).all(),
            label=_("Mark as old"),
            required=False,
            widget=forms.CheckboxSelectMultiple,
        )
        if not self.request_user.is_root:
            self.fields.pop("start_date")

    def clean_users(self):
        """
        Check that the user is not trying to add an user already in the club
        Also check that the user is valid and has a valid subscription
        """
        cleaned_data = super(ClubMemberForm, self).clean()
        users = []
        for user_id in cleaned_data["users"]:
            user = User.objects.filter(id=user_id).first()
            if not user:
                raise forms.ValidationError(
                    _("One of the selected users doesn't exist"), code="invalid"
                )
            if not user.is_subscribed:
                raise forms.ValidationError(
                    _("User must be subscriber to take part to a club"), code="invalid"
                )
            if self.club.get_membership_for(user):
                raise forms.ValidationError(
                    _("You can not add the same user twice"), code="invalid"
                )
            users.append(user)
        return users

    def clean(self):
        """
        Check user rights for adding an user
        """
        cleaned_data = super(ClubMemberForm, self).clean()

        if "start_date" in cleaned_data and not cleaned_data["start_date"]:
            # Drop start_date if allowed to edition but not specified
            cleaned_data.pop("start_date")

        if not cleaned_data.get("users"):
            # No user to add equals no check needed
            return cleaned_data

        if cleaned_data.get("role", "") == "":
            # Role is required if users exists
            self.add_error("role", _("You should specify a role"))
            return cleaned_data

        request_user = self.request_user
        membership = self.request_user_membership
        if not (
            cleaned_data["role"] <= settings.SITH_MAXIMUM_FREE_ROLE
            or (membership is not None and membership.role >= cleaned_data["role"])
            or request_user.is_board_member
            or request_user.is_root
        ):
            raise forms.ValidationError(_("You do not have the permission to do that"))
        return cleaned_data
