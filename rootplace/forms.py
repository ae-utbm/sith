from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from core.models import BanGroup, User, UserBan
from core.views.forms import FutureDateTimeField, SelectDate, SelectDateTime
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


class BanReportForm(forms.Form):
    """Form to generate a PDF report of banned users at a specific date."""

    DISPLAY_MODES = [
        ("image", _("Images (profile pictures and names below)")),
        ("desc", _("Detailed (name, type and profile picture)")),
    ]

    LANGUAGES = [
        ("fr", _("French")),
        ("en", _("English")),
    ]

    date = forms.DateField(
        label=_("Date"),
        help_text=_("Select the date to view banned users"),
        required=True,
        widget=SelectDate,
    )
    ban_group = forms.ModelChoiceField(
        label=_("Ban type (optional)"),
        help_text=_("Filter by ban type. Leave empty to show all bans."),
        required=False,
        queryset=BanGroup.objects.all(),
        empty_label=_("All ban types"),
    )
    language = forms.ChoiceField(
        label=_("Language"),
        choices=LANGUAGES,
        initial="fr",
        help_text=_("Language for the PDF report"),
    )
    mode = forms.ChoiceField(
        label=_("Display mode"),
        choices=DISPLAY_MODES,
        initial="desc",
        widget=forms.RadioSelect,
    )

