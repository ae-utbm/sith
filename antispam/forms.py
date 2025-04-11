from django import forms
from django.core.validators import EmailValidator
from django.utils.translation import gettext_lazy as _

from antispam.models import ToxicDomain


class AntiSpamEmailValidator(EmailValidator):
    def __call__(self, value: str):
        super().__call__(value)
        domain_part = value.rsplit("@", 1)[1]
        if ToxicDomain.objects.filter(domain=domain_part).exists():
            raise forms.ValidationError(_("Email domain is not allowed."))


validate_antispam_email = AntiSpamEmailValidator()


class AntiSpamEmailField(forms.EmailField):
    """An email field that email addresses with a known toxic domain."""

    default_validators = [validate_antispam_email]
