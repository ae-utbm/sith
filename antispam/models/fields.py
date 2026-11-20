from django.conf import settings
from django.db import models

from antispam import forms


class AntiSpamEmailField(models.EmailField):
    """An email field that forbids email addresses with a known toxic domain."""

    default_validators = [forms.validate_antispam_email]


if settings.TESTING:
    from model_bakery import baker

    baker.generators.add(
        AntiSpamEmailField, lambda: baker.random_gen.gen_email(max_length=100)
    )
else:  # pragma: no cover
    # baker is only used in tests, so we don't need coverage for this part
    pass
