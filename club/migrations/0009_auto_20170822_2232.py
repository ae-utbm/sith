# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("club", "0008_auto_20170515_2214"),
    ]

    operations = [
        migrations.CreateModel(
            name="Mailing",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        verbose_name="ID",
                        serialize=False,
                        primary_key=True,
                    ),
                ),
                (
                    "email",
                    models.CharField(
                        max_length=256,
                        unique=True,
                        validators=[
                            django.core.validators.RegexValidator(
                                re.compile(
                                    "(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*\\Z|^\"([\\001-\\010\\013\\014\\016-\\037!#-\\[\\]-\\177]|\\\\[\\001-\\011\\013\\014\\016-\\177])*\"\\Z)",
                                    34,
                                ),
                                "Enter a valid address. Only the root of the address is needed.",
                            )
                        ],
                        verbose_name="Email address",
                    ),
                ),
                (
                    "is_moderated",
                    models.BooleanField(default=False, verbose_name="is moderated"),
                ),
                (
                    "club",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        verbose_name="Club",
                        related_name="mailings",
                        to="club.Club",
                    ),
                ),
                (
                    "moderator",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        null=True,
                        verbose_name="moderator",
                        related_name="moderated_mailings",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="MailingSubscription",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        verbose_name="ID",
                        serialize=False,
                        primary_key=True,
                    ),
                ),
                (
                    "email",
                    models.EmailField(max_length=254, verbose_name="Email address"),
                ),
                (
                    "mailing",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        verbose_name="Mailing",
                        related_name="subscriptions",
                        to="club.Mailing",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        null=True,
                        verbose_name="User",
                        related_name="mailing_subscriptions",
                        blank=True,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.AlterUniqueTogether(
            name="mailingsubscription",
            unique_together=set([("user", "email", "mailing")]),
        ),
    ]
