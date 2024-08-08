import re

from django import forms
from django.core.validators import EmailValidator
from django.utils.translation import gettext_lazy as _

from antispam.models import ToxicDomain


class AntiSpamEmailField(forms.EmailField):
    """An email field that email addresses with a known toxic domain."""

    def run_validators(self, value: str):
        super().run_validators(value)
        # Domain part should exist since email validation is guaranteed to run first
        domain = re.search(EmailValidator.domain_regex, value)
        if ToxicDomain.objects.filter(domain=domain[0]).exists():
            raise forms.ValidationError(_("Email domain is not allowed."))
