# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import accounting.models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("counter", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="CashRegisterSummary",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        primary_key=True,
                        serialize=False,
                        auto_created=True,
                    ),
                ),
                ("date", models.DateTimeField(verbose_name="date")),
                (
                    "comment",
                    models.TextField(null=True, verbose_name="comment", blank=True),
                ),
                ("emptied", models.BooleanField(default=False, verbose_name="emptied")),
                (
                    "counter",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="counter.Counter",
                        related_name="cash_summaries",
                        verbose_name="counter",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                        related_name="cash_summaries",
                        verbose_name="user",
                    ),
                ),
            ],
            options={"verbose_name": "cash register summary"},
        ),
        migrations.CreateModel(
            name="CashRegisterSummaryItem",
            fields=[
                (
                    "id",
                    models.AutoField(
                        verbose_name="ID",
                        primary_key=True,
                        serialize=False,
                        auto_created=True,
                    ),
                ),
                (
                    "value",
                    accounting.models.CurrencyField(
                        max_digits=12, verbose_name="value", decimal_places=2
                    ),
                ),
                ("quantity", models.IntegerField(default=0, verbose_name="quantity")),
                ("check", models.BooleanField(default=False, verbose_name="check")),
                (
                    "cash_summary",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="counter.CashRegisterSummary",
                        related_name="items",
                        verbose_name="cash summary",
                    ),
                ),
            ],
            options={"verbose_name": "cash register summary item"},
        ),
        migrations.AlterField(
            model_name="permanency",
            name="counter",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="counter.Counter",
                related_name="permanencies",
                verbose_name="counter",
            ),
        ),
        migrations.AlterField(
            model_name="permanency",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
                related_name="permanencies",
                verbose_name="user",
            ),
        ),
    ]
