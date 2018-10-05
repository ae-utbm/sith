# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("subscription", "0001_initial"), ("counter", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="Launderette",
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
                    "counter",
                    models.OneToOneField(
                        related_name="launderette",
                        verbose_name="counter",
                        to="counter.Counter",
                    ),
                ),
            ],
            options={"verbose_name": "Launderette"},
        ),
        migrations.CreateModel(
            name="Machine",
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
                    "type",
                    models.CharField(
                        choices=[("WASHING", "Washing"), ("DRYING", "Drying")],
                        max_length=10,
                        verbose_name="type",
                    ),
                ),
                (
                    "is_working",
                    models.BooleanField(verbose_name="is working", default=True),
                ),
                (
                    "launderette",
                    models.ForeignKey(
                        verbose_name="launderette",
                        to="launderette.Launderette",
                        related_name="machines",
                    ),
                ),
            ],
            options={"verbose_name": "Machine"},
        ),
        migrations.CreateModel(
            name="Slot",
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
                ("start_date", models.DateTimeField(verbose_name="start date")),
                (
                    "type",
                    models.CharField(
                        choices=[("WASHING", "Washing"), ("DRYING", "Drying")],
                        max_length=10,
                        verbose_name="type",
                    ),
                ),
                (
                    "machine",
                    models.ForeignKey(
                        verbose_name="machine",
                        to="launderette.Machine",
                        related_name="slots",
                    ),
                ),
            ],
            options={"verbose_name": "Slot", "ordering": ["start_date"]},
        ),
        migrations.CreateModel(
            name="Token",
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
                ("name", models.CharField(max_length=5, verbose_name="name")),
                (
                    "type",
                    models.CharField(
                        choices=[("WASHING", "Washing"), ("DRYING", "Drying")],
                        max_length=10,
                        verbose_name="type",
                    ),
                ),
                (
                    "borrow_date",
                    models.DateTimeField(
                        null=True, verbose_name="borrow date", blank=True
                    ),
                ),
                (
                    "launderette",
                    models.ForeignKey(
                        verbose_name="launderette",
                        to="launderette.Launderette",
                        related_name="tokens",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        null=True,
                        related_name="tokens",
                        verbose_name="user",
                        to="core.User",
                        blank=True,
                    ),
                ),
            ],
            options={"verbose_name": "Token", "ordering": ["type", "name"]},
        ),
        migrations.AddField(
            model_name="slot",
            name="token",
            field=models.ForeignKey(
                null=True,
                related_name="slots",
                verbose_name="token",
                to="launderette.Token",
                blank=True,
            ),
        ),
        migrations.AddField(
            model_name="slot",
            name="user",
            field=models.ForeignKey(
                verbose_name="user", to="core.User", related_name="slots"
            ),
        ),
        migrations.AlterUniqueTogether(
            name="token", unique_together=set([("name", "launderette", "type")])
        ),
    ]
