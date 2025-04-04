from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from core.models import User, UserBan
from core.views.forms import FutureDateTimeField, SelectDateTime
from core.views.widgets.ajax_select import AutoCompleteSelectUser


class MergeForm(forms.Form):
    user1 = forms.ModelChoiceField(
        label=_("User that will be kept"),
        help_text=None,
        required=True,
        widget=AutoCompleteSelectUser,
        queryset=User.objects.all(),
    )
    user2 = forms.ModelChoiceField(
        label=_("User that will be deleted"),
        help_text=None,
        required=True,
        widget=AutoCompleteSelectUser,
        queryset=User.objects.all(),
    )

    def clean(self):
        cleaned_data = super().clean()
        user1 = cleaned_data.get("user1")
        user2 = cleaned_data.get("user2")

        if user1.id == user2.id:
            raise ValidationError(_("You cannot merge two identical users."))

        return cleaned_data


class SelectUserForm(forms.Form):
    user = forms.ModelChoiceField(
        label=_("User to be selected"),
        help_text=None,
        required=True,
        widget=AutoCompleteSelectUser,
        queryset=User.objects.all(),
    )


class BanForm(forms.ModelForm):
    """Form to ban a user."""

    required_css_class = "required"

    class Meta:
        model = UserBan
        fields = ["user", "ban_group", "reason", "expires_at"]
        field_classes = {"expires_at": FutureDateTimeField}
        widgets = {
            "user": AutoCompleteSelectUser,
            "ban_group": forms.RadioSelect,
            "expires_at": SelectDateTime,
        }
