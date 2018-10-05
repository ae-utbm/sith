# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.core.validators
import accounting.models


class Migration(migrations.Migration):

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="AccountingType",
            fields=[
                (
                    "id",
                    models.AutoField(
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                        auto_created=True,
                    ),
                ),
                (
                    "code",
                    models.CharField(
                        max_length=16,
                        verbose_name="code",
                        validators=[
                            django.core.validators.RegexValidator(
                                "^[0-9]*$",
                                "An accounting type code contains only numbers",
                            )
                        ],
                    ),
                ),
                ("label", models.CharField(max_length=128, verbose_name="label")),
                (
                    "movement_type",
                    models.CharField(
                        choices=[
                            ("CREDIT", "Credit"),
                            ("DEBIT", "Debit"),
                            ("NEUTRAL", "Neutral"),
                        ],
                        max_length=12,
                        verbose_name="movement type",
                    ),
                ),
            ],
            options={
                "verbose_name": "accounting type",
                "ordering": ["movement_type", "code"],
            },
        ),
        migrations.CreateModel(
            name="BankAccount",
            fields=[
                (
                    "id",
                    models.AutoField(
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                        auto_created=True,
                    ),
                ),
                ("name", models.CharField(max_length=30, verbose_name="name")),
                (
                    "iban",
                    models.CharField(max_length=255, blank=True, verbose_name="iban"),
                ),
                (
                    "number",
                    models.CharField(
                        max_length=255, blank=True, verbose_name="account number"
                    ),
                ),
            ],
            options={"verbose_name": "Bank account", "ordering": ["club", "name"]},
        ),
        migrations.CreateModel(
            name="ClubAccount",
            fields=[
                (
                    "id",
                    models.AutoField(
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                        auto_created=True,
                    ),
                ),
                ("name", models.CharField(max_length=30, verbose_name="name")),
            ],
            options={
                "verbose_name": "Club account",
                "ordering": ["bank_account", "name"],
            },
        ),
        migrations.CreateModel(
            name="Company",
            fields=[
                (
                    "id",
                    models.AutoField(
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                        auto_created=True,
                    ),
                ),
                ("name", models.CharField(max_length=60, verbose_name="name")),
            ],
            options={"verbose_name": "company"},
        ),
        migrations.CreateModel(
            name="GeneralJournal",
            fields=[
                (
                    "id",
                    models.AutoField(
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                        auto_created=True,
                    ),
                ),
                ("start_date", models.DateField(verbose_name="start date")),
                (
                    "end_date",
                    models.DateField(
                        null=True, verbose_name="end date", default=None, blank=True
                    ),
                ),
                ("name", models.CharField(max_length=40, verbose_name="name")),
                (
                    "closed",
                    models.BooleanField(verbose_name="is closed", default=False),
                ),
                (
                    "amount",
                    accounting.models.CurrencyField(
                        decimal_places=2,
                        default=0,
                        verbose_name="amount",
                        max_digits=12,
                    ),
                ),
                (
                    "effective_amount",
                    accounting.models.CurrencyField(
                        decimal_places=2,
                        default=0,
                        verbose_name="effective_amount",
                        max_digits=12,
                    ),
                ),
            ],
            options={"verbose_name": "General journal", "ordering": ["-start_date"]},
        ),
        migrations.CreateModel(
            name="Operation",
            fields=[
                (
                    "id",
                    models.AutoField(
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                        auto_created=True,
                    ),
                ),
                ("number", models.IntegerField(verbose_name="number")),
                (
                    "amount",
                    accounting.models.CurrencyField(
                        decimal_places=2, max_digits=12, verbose_name="amount"
                    ),
                ),
                ("date", models.DateField(verbose_name="date")),
                ("remark", models.CharField(max_length=128, verbose_name="comment")),
                (
                    "mode",
                    models.CharField(
                        choices=[
                            ("CHECK", "Check"),
                            ("CASH", "Cash"),
                            ("TRANSFERT", "Transfert"),
                            ("CARD", "Credit card"),
                        ],
                        max_length=255,
                        verbose_name="payment method",
                    ),
                ),
                (
                    "cheque_number",
                    models.CharField(
                        max_length=32,
                        null=True,
                        verbose_name="cheque number",
                        default="",
                        blank=True,
                    ),
                ),
                ("done", models.BooleanField(verbose_name="is done", default=False)),
                (
                    "target_type",
                    models.CharField(
                        choices=[
                            ("USER", "User"),
                            ("CLUB", "Club"),
                            ("ACCOUNT", "Account"),
                            ("COMPANY", "Company"),
                            ("OTHER", "Other"),
                        ],
                        max_length=10,
                        verbose_name="target type",
                    ),
                ),
                (
                    "target_id",
                    models.IntegerField(
                        null=True, verbose_name="target id", blank=True
                    ),
                ),
                (
                    "target_label",
                    models.CharField(
                        max_length=32,
                        blank=True,
                        verbose_name="target label",
                        default="",
                    ),
                ),
                (
                    "accounting_type",
                    models.ForeignKey(
                        null=True,
                        related_name="operations",
                        verbose_name="accounting type",
                        to="accounting.AccountingType",
                        blank=True,
                    ),
                ),
            ],
            options={"ordering": ["-number"]},
        ),
        migrations.CreateModel(
            name="SimplifiedAccountingType",
            fields=[
                (
                    "id",
                    models.AutoField(
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                        auto_created=True,
                    ),
                ),
                ("label", models.CharField(max_length=128, verbose_name="label")),
                (
                    "accounting_type",
                    models.ForeignKey(
                        verbose_name="simplified accounting types",
                        to="accounting.AccountingType",
                        related_name="simplified_types",
                    ),
                ),
            ],
            options={
                "verbose_name": "simplified type",
                "ordering": ["accounting_type__movement_type", "accounting_type__code"],
            },
        ),
    ]
