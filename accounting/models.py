#
# Copyright 2023 © AE UTBM
# ae@utbm.fr / ae.info@utbm.fr
#
# This file is part of the website of the UTBM Student Association (AE UTBM),
# https://ae.utbm.fr.
#
# You can find the source code of the website at https://github.com/ae-utbm/sith
#
# LICENSED UNDER THE GNU GENERAL PUBLIC LICENSE VERSION 3 (GPLv3)
# SEE : https://raw.githubusercontent.com/ae-utbm/sith/master/LICENSE
# OR WITHIN THE LOCAL FILE "LICENSE"
#
#

from decimal import Decimal

from django.conf import settings
from django.core import validators
from django.db import models
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField

from club.models import Club
from core.models import SithFile


class CurrencyField(models.DecimalField):
    """Custom database field used for currency."""

    def __init__(self, *args, **kwargs):
        kwargs["max_digits"] = 12
        kwargs["decimal_places"] = 2
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        try:
            return super().to_python(value).quantize(Decimal("0.01"))
        except AttributeError:
            return None


if settings.TESTING:
    from model_bakery import baker

    baker.generators.add(
        CurrencyField,
        lambda: baker.random_gen.gen_decimal(max_digits=8, decimal_places=2),
    )
else:  # pragma: no cover
    # baker is only used in tests, so we don't need coverage for this part
    pass


# Accounting classes


class Company(models.Model):
    name = models.CharField(_("name"), max_length=60)
    street = models.CharField(_("street"), max_length=60, blank=True)
    city = models.CharField(_("city"), max_length=60, blank=True)
    postcode = models.CharField(_("postcode"), max_length=10, blank=True)
    country = models.CharField(_("country"), max_length=32, blank=True)
    phone = PhoneNumberField(_("phone"), blank=True)
    email = models.EmailField(_("email"), blank=True)
    website = models.CharField(_("website"), max_length=64, blank=True)

    class Meta:
        verbose_name = _("company")

    def __str__(self):
        return self.name


class BankAccount(models.Model):
    name = models.CharField(_("name"), max_length=30)
    iban = models.CharField(_("iban"), max_length=255, blank=True)
    number = models.CharField(_("account number"), max_length=255, blank=True)
    club = models.ForeignKey(
        Club,
        related_name="bank_accounts",
        verbose_name=_("club"),
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = _("Bank account")
        ordering = ["club", "name"]

    def __str__(self):
        return self.name


class ClubAccount(models.Model):
    name = models.CharField(_("name"), max_length=30)
    club = models.ForeignKey(
        Club,
        related_name="club_account",
        verbose_name=_("club"),
        on_delete=models.CASCADE,
    )
    bank_account = models.ForeignKey(
        BankAccount,
        related_name="club_accounts",
        verbose_name=_("bank account"),
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = _("Club account")
        ordering = ["bank_account", "name"]

    def __str__(self):
        return self.name


class GeneralJournal(models.Model):
    """Class storing all the operations for a period of time."""

    start_date = models.DateField(_("start date"))
    end_date = models.DateField(_("end date"), null=True, blank=True, default=None)
    name = models.CharField(_("name"), max_length=40)
    closed = models.BooleanField(_("is closed"), default=False)
    club_account = models.ForeignKey(
        ClubAccount,
        related_name="journals",
        null=False,
        verbose_name=_("club account"),
        on_delete=models.CASCADE,
    )
    amount = CurrencyField(_("amount"), default=0)
    effective_amount = CurrencyField(_("effective_amount"), default=0)

    class Meta:
        verbose_name = _("General journal")
        ordering = ["-start_date"]

    def __str__(self):
        return self.name


class Operation(models.Model):
    """An operation is a line in the journal, a debit or a credit."""

    number = models.IntegerField(_("number"))
    journal = models.ForeignKey(
        GeneralJournal,
        related_name="operations",
        null=False,
        verbose_name=_("journal"),
        on_delete=models.CASCADE,
    )
    amount = CurrencyField(_("amount"))
    date = models.DateField(_("date"))
    remark = models.CharField(_("comment"), max_length=128, null=True, blank=True)
    mode = models.CharField(
        _("payment method"),
        max_length=255,
        choices=settings.SITH_ACCOUNTING_PAYMENT_METHOD,
    )
    cheque_number = models.CharField(
        _("cheque number"), max_length=32, default="", null=True, blank=True
    )
    invoice = models.ForeignKey(
        SithFile,
        related_name="operations",
        verbose_name=_("invoice"),
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    done = models.BooleanField(_("is done"), default=False)
    simpleaccounting_type = models.ForeignKey(
        "SimplifiedAccountingType",
        related_name="operations",
        verbose_name=_("simple type"),
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    accounting_type = models.ForeignKey(
        "AccountingType",
        related_name="operations",
        verbose_name=_("accounting type"),
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    label = models.ForeignKey(
        "Label",
        related_name="operations",
        verbose_name=_("label"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    target_type = models.CharField(
        _("target type"),
        max_length=10,
        choices=[
            ("USER", _("User")),
            ("CLUB", _("Club")),
            ("ACCOUNT", _("Account")),
            ("COMPANY", _("Company")),
            ("OTHER", _("Other")),
        ],
    )
    target_id = models.IntegerField(_("target id"), null=True, blank=True)
    target_label = models.CharField(
        _("target label"), max_length=32, default="", blank=True
    )
    linked_operation = models.OneToOneField(
        "self",
        related_name="operation_linked_to",
        verbose_name=_("linked operation"),
        null=True,
        blank=True,
        default=None,
        on_delete=models.CASCADE,
    )

    class Meta:
        unique_together = ("number", "journal")
        ordering = ["-number"]

    def __str__(self):
        return f"{self.amount} € | {self.date} | {self.accounting_type} | {self.done}"


class AccountingType(models.Model):
    """Accounting types.

    Those are numbers used in accounting to classify operations
    """

    code = models.CharField(
        _("code"),
        max_length=16,
        validators=[
            validators.RegexValidator(
                r"^[0-9]*$", _("An accounting type code contains only numbers")
            )
        ],
    )
    label = models.CharField(_("label"), max_length=128)
    movement_type = models.CharField(
        _("movement type"),
        choices=[
            ("CREDIT", _("Credit")),
            ("DEBIT", _("Debit")),
            ("NEUTRAL", _("Neutral")),
        ],
        max_length=12,
    )

    class Meta:
        verbose_name = _("accounting type")
        ordering = ["movement_type", "code"]

    def __str__(self):
        return self.code + " - " + self.get_movement_type_display() + " - " + self.label


class SimplifiedAccountingType(models.Model):
    """Simplified version of `AccountingType`."""

    label = models.CharField(_("label"), max_length=128)
    accounting_type = models.ForeignKey(
        AccountingType,
        related_name="simplified_types",
        verbose_name=_("simplified accounting types"),
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = _("simplified type")
        ordering = ["accounting_type__movement_type", "accounting_type__code"]

    def __str__(self):
        return (
            f"{self.get_movement_type_display()} "
            f"- {self.accounting_type.code} - {self.label}"
        )

    @property
    def movement_type(self):
        return self.accounting_type.movement_type

    def get_movement_type_display(self):
        return self.accounting_type.get_movement_type_display()


class Label(models.Model):
    """Label allow a club to sort its operations."""

    name = models.CharField(_("label"), max_length=64)
    club_account = models.ForeignKey(
        ClubAccount,
        related_name="labels",
        verbose_name=_("club account"),
        on_delete=models.CASCADE,
    )

    class Meta:
        unique_together = ("name", "club_account")

    def __str__(self):
        return "%s (%s)" % (self.name, self.club_account.name)
