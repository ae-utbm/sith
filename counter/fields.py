from decimal import Decimal

from django.conf import settings
from django.core import checks
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.functional import cached_property


class CurrencyField(models.DecimalField):
    """Custom database field used for currency."""

    def __init__(
        self, verbose_name=None, name=None, min_value=None, max_value=None, **kwargs
    ):
        kwargs.update({"max_digits": 12, "decimal_places": 2})
        self.min_value = min_value
        self.max_value = max_value
        super().__init__(verbose_name, name, **kwargs)

    def to_python(self, value):
        if value is None:
            return None
        return super().to_python(value).quantize(Decimal("0.01"))

    @cached_property
    def validators(self):
        res = []
        if self.max_value:
            res.append(MaxValueValidator(self.max_value))
        if self.min_value:
            res.append(MinValueValidator(self.min_value))
        return [*super().validators, *res]

    def check(self, **kwargs):  # pragma: no cover
        # this is executed during runserver, but won't run in prod
        errors = super().check(**kwargs)
        for name, val in ("min_value", self.min_value), ("max_value", self.max_value):
            if not val:
                continue
            try:
                float(val)
            except ValueError:
                errors.append(
                    checks.Error(
                        f"CurrencyField.{name} must be a valid float",
                        obj=self,
                        id="sith.E001",
                    )
                )
        return errors

    def formfield(self, **kwargs):
        return super().formfield(
            **{"min_value": self.min_value, "max_value": self.max_value, **kwargs}
        )

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if self.min_value is not None:
            kwargs["min_value"] = self.min_value
        if self.max_value is not None:
            kwargs["max_value"] = self.max_value
        return name, path, args, kwargs


if settings.TESTING:
    from model_bakery import baker

    baker.generators.add(
        CurrencyField,
        lambda: baker.random_gen.gen_decimal(max_digits=8, decimal_places=2),
    )
else:  # pragma: no cover
    # baker is only used in tests, so we don't need coverage for this part
    pass
