import secrets
from typing import Any

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from core.models import User
from core.views.forms import SelectDate, SelectDateTime
from core.views.widgets.ajax_select import AutoCompleteSelectUser
from subscription.models import Subscription


class SelectionDateForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["start_date"] = forms.DateTimeField(
            label=_("Start date"), widget=SelectDateTime, required=True
        )
        self.fields["end_date"] = forms.DateTimeField(
            label=_("End date"), widget=SelectDateTime, required=True
        )


class SubscriptionForm(forms.ModelForm):
    def __init__(self, *args, initial=None, **kwargs):
        initial = initial or {}
        if "subscription_type" not in initial:
            initial["subscription_type"] = "deux-semestres"
        if "payment_method" not in initial:
            initial["payment_method"] = "CARD"
        super().__init__(*args, initial=initial, **kwargs)

    def save(self, *args, **kwargs):
        if self.errors:
            # let django deal with the error messages
            return super().save(*args, **kwargs)

        duration, user = self.instance.semester_duration, self.instance.member
        self.instance.subscription_start = self.instance.compute_start(
            duration=duration, user=user
        )
        self.instance.subscription_end = self.instance.compute_end(
            duration=duration, start=self.instance.subscription_start, user=user
        )
        return super().save(*args, **kwargs)


class SubscriptionNewUserForm(SubscriptionForm):
    """Form to create subscriptions with the user they belong to.

    Examples:
        ```py
        assert not User.objects.filter(email=request.POST.get("email")).exists()
        form = SubscriptionNewUserForm(request.POST)
        if form.is_valid():
            form.save()

        # now the user exists and is subscribed
        user = User.objects.get(email=request.POST.get("email"))
        assert user.is_subscribed
    """

    template_name = "subscription/forms/create_new_user.html"

    __user_fields = forms.fields_for_model(
        User,
        ["first_name", "last_name", "email", "date_of_birth"],
        widgets={"date_of_birth": SelectDate},
    )
    first_name = __user_fields["first_name"]
    last_name = __user_fields["last_name"]
    email = __user_fields["email"]
    date_of_birth = __user_fields["date_of_birth"]

    class Meta:
        model = Subscription
        fields = ["subscription_type", "payment_method", "location"]

    field_order = [
        "first_name",
        "last_name",
        "email",
        "date_of_birth",
        "subscription_type",
        "payment_method",
        "location",
    ]

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            raise ValidationError(_("A user with that email address already exists"))
        return email

    def clean(self) -> dict[str, Any]:
        """Initialize the [User][core.models.User] linked to this subscription.

        Warning:
            The `User` is initialized, but not saved.
            Don't use it for operations that expect
            a persisted object.
        """
        member = User(
            first_name=self.cleaned_data.get("first_name"),
            last_name=self.cleaned_data.get("last_name"),
            email=self.cleaned_data.get("email"),
            date_of_birth=self.cleaned_data.get("date_of_birth"),
        )
        if self.cleaned_data.get("subscription_type") in [
            "un-semestre",
            "deux-semestres",
            "cursus-tronc-commun",
            "cursus-branche",
        ]:
            member.role = "STUDENT"
        member.generate_username()
        member.set_password(secrets.token_urlsafe(nbytes=10))
        self.instance.member = member
        return super().clean()

    def save(self, *args, **kwargs):
        if self.errors:
            # let django deal with the error messages
            return super().save(*args, **kwargs)
        self.instance.member.save()
        return super().save(*args, **kwargs)


class SubscriptionExistingUserForm(SubscriptionForm):
    """Form to add a subscription to an existing user."""

    template_name = "subscription/forms/create_existing_user.html"
    required_css_class = "required"

    birthdate = forms.fields_for_model(
        User,
        ["date_of_birth"],
        widgets={"date_of_birth": SelectDate(attrs={"hidden": True})},
        help_texts={"date_of_birth": _("This user didn't fill its birthdate yet.")},
    )["date_of_birth"]

    class Meta:
        model = Subscription
        fields = ["member", "subscription_type", "payment_method", "location"]
        widgets = {"member": AutoCompleteSelectUser}

    field_order = [
        "member",
        "birthdate",
        "subscription_type",
        "payment_method",
        "location",
    ]

    def __init__(self, *args, initial=None, **kwargs):
        super().__init__(*args, initial=initial, **kwargs)
        self.fields["birthdate"].required = True
        if not initial:
            return
        member = initial.get("member")
        if member:
            member = User.objects.filter(id=member).first()
        if member and member.date_of_birth:
            # if there is an initial member with a birthdate,
            # there is no need to ask this to the user
            self.fields["birthdate"].initial = member.date_of_birth
        elif member:
            # if there is an initial member without a birthdate,
            # then the field must be displayed
            self.fields["birthdate"].widget.attrs.update({"hidden": False})
        # if there is no initial member, it means that it will be
        # dynamically selected using the AutoCompleteSelectUser widget.
        # JS will take care of un-hiding the field if necessary

    def save(self, *args, **kwargs):
        if self.errors:
            return super().save(*args, **kwargs)
        if (
            self.cleaned_data["birthdate"] is not None
            and self.instance.member.date_of_birth != self.cleaned_data["birthdate"]
        ):
            self.instance.member.date_of_birth = self.cleaned_data["birthdate"]
            self.instance.member.save()
        return super().save(*args, **kwargs)
