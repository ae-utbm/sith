#
# Copyright 2016,2017
# - Skia <skia@libskia.so>
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

from django import forms
from django.db.models import Exists, OuterRef, Q, QuerySet
from django.db.models.functions import Lower
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from club.models import Club, ClubRole, Mailing, MailingSubscription, Membership
from core.models import User
from core.views.forms import SelectDateTime
from core.views.widgets.ajax_select import (
    AutoCompleteSelectMultipleUser,
    AutoCompleteSelectUser,
)
from counter.models import Counter, Selling
from counter.schemas import SaleFilterSchema


class ClubEditForm(forms.ModelForm):
    error_css_class = "error"
    required_css_class = "required"

    class Meta:
        model = Club
        fields = ["address", "logo", "short_description"]
        widgets = {"short_description": forms.Textarea()}


class ClubAdminEditForm(ClubEditForm):
    admin_fields = ["name", "parent", "is_active"]

    class Meta(ClubEditForm.Meta):
        fields = ["name", "parent", "is_active", *ClubEditForm.Meta.fields]


class MailingForm(forms.Form):
    """Form handling mailing lists right."""

    ACTION_NEW_MAILING = 1
    ACTION_NEW_SUBSCRIPTION = 2
    ACTION_REMOVE_SUBSCRIPTION = 3

    subscription_users = forms.ModelMultipleChoiceField(
        label=_("Users to add"),
        help_text=_("Search users to add (one or more)."),
        required=False,
        widget=AutoCompleteSelectMultipleUser,
        queryset=User.objects.all(),
    )

    def __init__(self, club_id, user_id, mailings, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
        """If the given field doesn't exist or has no value, add a required error on it."""
        if not cleaned_data.get(field, None):
            self.add_error(field, _("This field is required"))

    def clean_subscription_users(self):
        """Convert given users into real users and check their validity."""
        cleaned_data = super().clean()
        users = []
        for user in cleaned_data["subscription_users"]:
            if not user.email:
                raise forms.ValidationError(
                    _("One of the selected users doesn't have an email address"),
                    code="invalid",
                )
            users.append(user)
        return users

    def clean(self):
        cleaned_data = super().clean()

        if "action" not in cleaned_data:
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
    begin_date = forms.DateTimeField(
        label=_("Begin date"), widget=SelectDateTime, required=False
    )
    end_date = forms.DateTimeField(
        label=_("End date"), widget=SelectDateTime, required=False
    )

    def __init__(self, club, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # postgres struggles really hard with a single query having three WHERE conditions,
        # but deals perfectly fine with UNION of multiple queryset with their own WHERE clause,
        # so we do this to get the ids, which we use to build another queryset that can be used by django.
        club_sales_subquery = Selling.objects.filter(counter=OuterRef("pk"), club=club)
        ids = (
            Counter.objects.filter(Q(club=club) | Q(products__club=club))
            .union(Counter.objects.filter(Exists(club_sales_subquery)))
            .values_list("id", flat=True)
        )
        counters_qs = Counter.objects.filter(id__in=ids).order_by(Lower("name"))
        self.fields["counters"] = forms.ModelMultipleChoiceField(
            counters_qs, label=_("Counter"), required=False
        )
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

    def to_filter_schema(self) -> SaleFilterSchema:
        products = (
            *self.cleaned_data["products"],
            *self.cleaned_data["archived_products"],
        )
        return SaleFilterSchema(
            after=self.cleaned_data["begin_date"],
            before=self.cleaned_data["end_date"],
            counters={c.id for c in self.cleaned_data["counters"]} or None,
            products={p.id for p in products} or None,
        )


class ClubOldMemberForm(forms.Form):
    members_old = forms.ModelMultipleChoiceField(
        Membership.objects.none(),
        label=_("Mark as old"),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    def __init__(self, *args, user: User, club: Club, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["members_old"].queryset = club.members.ongoing().editable_by(user)


class ClubMemberForm(forms.ModelForm):
    """Form to add a member to the club, as a board member."""

    error_css_class = "error"
    required_css_class = "required"

    class Meta:
        model = Membership
        fields = ["role", "description"]

    def __init__(self, *args, club: Club, request_user: User, **kwargs):
        self.club = club
        self.request_user = request_user
        self.request_user_membership = self.club.get_membership_for(self.request_user)
        super().__init__(*args, **kwargs)
        self.fields["role"].queryset = self.available_roles
        self.instance.club = club

    @property
    def available_roles(self) -> QuerySet[ClubRole]:
        """The roles that will be obtainable with this form."""
        # this is unreachable, because it will be overridden by subclasses
        return ClubRole.objects.none()  # pragma: no cover


class ClubAddMemberForm(ClubMemberForm):
    """Form to add a member to the club, as a board member."""

    class Meta(ClubMemberForm.Meta):
        fields = ["user", *ClubMemberForm.Meta.fields]
        widgets = {"user": AutoCompleteSelectUser}

    @cached_property
    def available_roles(self):
        """The roles that will be obtainable with this form.

        Admins and the club president can attribute any role.
        Board members can attribute roles lower than their own.
        Other users cannot attribute roles with this form
        """
        qs = self.club.roles.filter(is_active=True)
        if self.request_user.has_perm("club.add_membership"):
            return qs.all()
        membership = self.request_user_membership
        if membership is None or not membership.role.is_board:
            return ClubRole.objects.none()
        if membership.role.is_presidency:
            return qs.all()
        return qs.above_instance(membership.role)

    def clean_user(self):
        """Check that the user is not trying to add a user already in the club.

        Also check that the user is valid and has a valid subscription.
        """
        user = self.cleaned_data["user"]
        if not user.is_subscribed:
            raise forms.ValidationError(
                _("User must be subscriber to take part to a club"), code="invalid"
            )
        if self.club.get_membership_for(user):
            raise forms.ValidationError(
                _("You can not add the same user twice"), code="invalid"
            )
        return user


class JoinClubForm(ClubMemberForm):
    """Form to join a club."""

    def __init__(self, *args, club: Club, request_user: User, **kwargs):
        super().__init__(*args, club=club, request_user=request_user, **kwargs)
        self.instance.user = self.request_user

    @cached_property
    def available_roles(self):
        return self.club.roles.filter(is_board=False, is_active=True)

    def clean(self):
        """Check that the user is subscribed and isn't already in the club."""
        if not self.request_user.is_subscribed:
            raise forms.ValidationError(
                _("You must be subscribed to join a club"), code="invalid"
            )
        if self.club.get_membership_for(self.request_user):
            raise forms.ValidationError(
                _("You are already a member of this club"), code="invalid"
            )
        return super().clean()


class ClubSearchForm(forms.ModelForm):
    class Meta:
        model = Club
        fields = ["name"]
        widgets = {"name": forms.SearchInput(attrs={"autocomplete": "off"})}

    club_status = forms.NullBooleanField(
        label=_("Club status"),
        widget=forms.RadioSelect(
            choices=[(True, _("Active")), (False, _("Inactive")), ("", _("All clubs"))],
        ),
        initial=True,
    )

    def __init__(self, *args, data: dict | None = None, **kwargs):
        super().__init__(*args, data=data, **kwargs)
        if data is not None and "club_status" not in data:
            # if the key is missing, it is considered as None,
            # even though we want the default True value to be applied in such a case
            # so we enforce it.
            self.fields["club_status"].value = True
        self.fields["name"].required = False


class ClubRoleForm(forms.ModelForm):
    error_css_class = "error"
    required_css_class = "required"

    class Meta:
        model = ClubRole
        fields = ["name", "description", "is_presidency", "is_board", "is_active"]
        widgets = {
            "is_presidency": forms.HiddenInput(),
            "is_board": forms.HiddenInput(),
            "is_active": forms.CheckboxInput(attrs={"class": "switch"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        if "ORDER" in cleaned_data:
            self.instance.order = cleaned_data["ORDER"]
        return cleaned_data


class ClubRoleCreateForm(forms.ModelForm):
    """Form to create a club role.

    Notes:
        For UX purposes, users are not meant to fill `is_presidency`
        and `is_board`, so those values are required by the form constructor
        in order to initialize the instance properly.
    """

    error_css_class = "error"
    required_css_class = "required"

    class Meta:
        model = ClubRole
        fields = ["name", "description"]

    def __init__(
        self, *args, club: Club, is_presidency: bool, is_board: bool, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.instance.club = club
        self.instance.is_presidency = is_presidency
        self.instance.is_board = is_board


class ClubRoleBaseFormSet(forms.BaseInlineFormSet):
    ordering_widget = forms.HiddenInput()


ClubRoleFormSet = forms.inlineformset_factory(
    Club,
    ClubRole,
    ClubRoleForm,
    ClubRoleBaseFormSet,
    can_delete=False,
    can_order=True,
    edit_only=True,
    extra=0,
)
