# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import datetime
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("club", "0007_auto_20170324_0917"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Trombi",
            fields=[
                (
                    "id",
                    models.AutoField(
                        serialize=False,
                        auto_created=True,
                        verbose_name="ID",
                        primary_key=True,
                    ),
                ),
                (
                    "subscription_deadline",
                    models.DateField(
                        default=datetime.date.today,
                        help_text="Before this date, users are allowed to subscribe to this Trombi. After this date, users subscribed will be allowed to comment on each other.",
                        verbose_name="subscription deadline",
                    ),
                ),
                (
                    "comments_deadline",
                    models.DateField(
                        default=datetime.date.today,
                        help_text="After this date, users won't be able to make comments anymore.",
                        verbose_name="comments deadline",
                    ),
                ),
                (
                    "max_chars",
                    models.IntegerField(
                        default=400,
                        help_text="Maximum number of characters allowed in a comment.",
                        verbose_name="maximum characters",
                    ),
                ),
                ("club", models.OneToOneField(to="club.Club", related_name="trombi")),
            ],
        ),
        migrations.CreateModel(
            name="TrombiComment",
            fields=[
                (
                    "id",
                    models.AutoField(
                        serialize=False,
                        auto_created=True,
                        verbose_name="ID",
                        primary_key=True,
                    ),
                ),
                ("content", models.TextField(default="", verbose_name="content")),
            ],
        ),
        migrations.CreateModel(
            name="TrombiUser",
            fields=[
                (
                    "id",
                    models.AutoField(
                        serialize=False,
                        auto_created=True,
                        verbose_name="ID",
                        primary_key=True,
                    ),
                ),
                (
                    "profile_pict",
                    models.ImageField(
                        upload_to="trombi",
                        blank=True,
                        help_text="The profile picture you want in the trombi (warning: this picture may be published)",
                        verbose_name="profile pict",
                        null=True,
                    ),
                ),
                (
                    "scrub_pict",
                    models.ImageField(
                        upload_to="trombi",
                        blank=True,
                        help_text="The scrub picture you want in the trombi (warning: this picture may be published)",
                        verbose_name="scrub pict",
                        null=True,
                    ),
                ),
                (
                    "trombi",
                    models.ForeignKey(
                        to="trombi.Trombi",
                        blank=True,
                        verbose_name="trombi",
                        related_name="users",
                        on_delete=django.db.models.deletion.SET_NULL,
                        null=True,
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        verbose_name="trombi user",
                        to=settings.AUTH_USER_MODEL,
                        related_name="trombi_user",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="trombicomment",
            name="author",
            field=models.ForeignKey(
                to="trombi.TrombiUser",
                verbose_name="author",
                related_name="given_comments",
            ),
        ),
        migrations.AddField(
            model_name="trombicomment",
            name="target",
            field=models.ForeignKey(
                to="trombi.TrombiUser",
                verbose_name="target",
                related_name="received_comments",
            ),
        ),
    ]
