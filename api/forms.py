from django import forms
from django.forms import HiddenInput
from django.utils.translation import gettext_lazy as _


class ThirdPartyAuthForm(forms.Form):
    """Form to complete to authenticate on the sith from a third-party app.

    For the form to be valid, the user approve the EULA (french: CGU)
    and give its username from the third-party app.
    """

    cgu_accepted = forms.BooleanField(
        required=True,
        label=_("I have read and I accept the terms and conditions of use"),
        error_messages={
            "required": _("You must approve the terms and conditions of use.")
        },
    )
    is_username_valid = forms.BooleanField(
        required=True,
        error_messages={"required": _("You must confirm that this is your username.")},
    )
    client_id = forms.IntegerField(widget=HiddenInput())
    third_party_app = forms.CharField(widget=HiddenInput())
    cgu_link = forms.URLField(widget=HiddenInput())
    username = forms.CharField(widget=HiddenInput())
    callback_url = forms.URLField(widget=HiddenInput())
    signature = forms.CharField(widget=HiddenInput())

    def __init__(self, *args, label_suffix: str = "", initial, **kwargs):
        super().__init__(*args, label_suffix=label_suffix, initial=initial, **kwargs)
        self.fields["is_username_valid"].label = _(
            "I confirm that %(username)s is my username on %(app)s"
        ) % {"username": initial.get("username"), "app": initial.get("third_party_app")}
