from decimal import Decimal

from django.conf import settings
from django.db import models


class CurrencyField(models.DecimalField):
    """Custom database field used for currency."""

    def __init__(self, *args, **kwargs):
        kwargs["max_digits"] = 12
        kwargs["decimal_places"] = 2
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        if value is None:
            return None
        return super().to_python(value).quantize(Decimal("0.01"))


if settings.TESTING:
    from model_bakery import baker

    baker.generators.add(
        CurrencyField,
        lambda: baker.random_gen.gen_decimal(max_digits=8, decimal_places=2),
    )
else:  # pragma: no cover
    # baker is only used in tests, so we don't need coverage for this part
    pass
