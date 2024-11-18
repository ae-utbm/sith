import random

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from core.models import User
from core.views.forms import SelectDate, SelectDateTime
from core.views.widgets.select import AutoCompleteSelectUser
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
    class Meta:
        model = Subscription
        fields = ["member", "subscription_type", "payment_method", "location"]
        widgets = {"member": AutoCompleteSelectUser}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["member"].required = False
        self.fields |= forms.fields_for_model(
            User,
            fields=["first_name", "last_name", "email", "date_of_birth"],
            widgets={"date_of_birth": SelectDate},
        )

    def clean_member(self):
        subscriber = self.cleaned_data.get("member")
        if subscriber:
            subscriber = User.objects.filter(id=subscriber.id).first()
        return subscriber

    def clean(self):
        cleaned_data = super().clean()
        if (
            cleaned_data.get("member") is None
            and "last_name" not in self.errors.as_data()
            and "first_name" not in self.errors.as_data()
            and "email" not in self.errors.as_data()
            and "date_of_birth" not in self.errors.as_data()
        ):
            self.errors.pop("member", None)
            if self.errors:
                return cleaned_data
            if User.objects.filter(email=cleaned_data.get("email")).first() is not None:
                self.add_error(
                    "email",
                    ValidationError(_("A user with that email address already exists")),
                )
            else:
                u = User(
                    last_name=self.cleaned_data.get("last_name"),
                    first_name=self.cleaned_data.get("first_name"),
                    email=self.cleaned_data.get("email"),
                    date_of_birth=self.cleaned_data.get("date_of_birth"),
                )
                u.generate_username()
                u.set_password(str(random.randrange(1000000, 10000000)))
                u.save()
                cleaned_data["member"] = u
        elif cleaned_data.get("member") is not None:
            self.errors.pop("last_name", None)
            self.errors.pop("first_name", None)
            self.errors.pop("email", None)
            self.errors.pop("date_of_birth", None)
        if cleaned_data.get("member") is None:
            # This should be handled here,
            # but it is done in the Subscription model's clean method
            # TODO investigate why!
            raise ValidationError(
                _(
                    "You must either choose an existing "
                    "user or create a new one properly"
                )
            )
        return cleaned_data
