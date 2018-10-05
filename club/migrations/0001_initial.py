# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Club",
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
                ("name", models.CharField(max_length=64, verbose_name="name")),
                (
                    "unix_name",
                    models.CharField(
                        unique=True,
                        max_length=30,
                        error_messages={
                            "unique": "A club with that unix name already exists."
                        },
                        verbose_name="unix name",
                        validators=[
                            django.core.validators.RegexValidator(
                                "^[a-z0-9][a-z0-9._-]*[a-z0-9]$",
                                "Enter a valid unix name. This value may contain only letters, numbers ./-/_ characters.",
                            )
                        ],
                    ),
                ),
                ("address", models.CharField(max_length=254, verbose_name="address")),
            ],
        ),
        migrations.CreateModel(
            name="Membership",
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
                    "start_date",
                    models.DateField(verbose_name="start date", auto_now=True),
                ),
                (
                    "end_date",
                    models.DateField(null=True, verbose_name="end date", blank=True),
                ),
                (
                    "role",
                    models.IntegerField(
                        choices=[
                            (0, "Curious"),
                            (1, "Active member"),
                            (2, "Board member"),
                            (3, "IT supervisor"),
                            (4, "Secretary"),
                            (5, "Communication supervisor"),
                            (7, "Treasurer"),
                            (9, "Vice-President"),
                            (10, "President"),
                        ],
                        default=0,
                        verbose_name="role",
                    ),
                ),
                (
                    "description",
                    models.CharField(
                        max_length=128, blank=True, verbose_name="description"
                    ),
                ),
                (
                    "club",
                    models.ForeignKey(
                        verbose_name="club", to="club.Club", related_name="members"
                    ),
                ),
            ],
        ),
    ]
