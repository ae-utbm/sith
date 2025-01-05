from django import forms
from django.utils.translation import gettext_lazy as _

from core.models import User, UserBan
from core.views.forms import FutureDateTimeField, SelectDateTime
from core.views.widgets.select import AutoCompleteSelectUser


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
