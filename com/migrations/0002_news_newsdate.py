# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ("club", "0005_auto_20161120_1149"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("com", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="News",
            fields=[
                (
                    "id",
                    models.AutoField(
                        primary_key=True,
                        serialize=False,
                        auto_created=True,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=64, verbose_name="title")),
                ("summary", models.TextField(verbose_name="summary")),
                ("content", models.TextField(verbose_name="content")),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("NOTICE", "Notice"),
                            ("EVENT", "Event"),
                            ("WEEKLY", "Weekly"),
                            ("CALL", "Call"),
                        ],
                        default="EVENT",
                        max_length=16,
                        verbose_name="type",
                    ),
                ),
                (
                    "is_moderated",
                    models.BooleanField(default=False, verbose_name="is moderated"),
                ),
                (
                    "author",
                    models.ForeignKey(
                        related_name="owned_news",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="author",
                    ),
                ),
                (
                    "club",
                    models.ForeignKey(
                        related_name="news", to="club.Club", verbose_name="club"
                    ),
                ),
                (
                    "moderator",
                    models.ForeignKey(
                        related_name="moderated_news",
                        null=True,
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="moderator",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="NewsDate",
            fields=[
                (
                    "id",
                    models.AutoField(
                        primary_key=True,
                        serialize=False,
                        auto_created=True,
                        verbose_name="ID",
                    ),
                ),
                (
                    "start_date",
                    models.DateTimeField(
                        null=True, blank=True, verbose_name="start_date"
                    ),
                ),
                (
                    "end_date",
                    models.DateTimeField(
                        null=True, blank=True, verbose_name="end_date"
                    ),
                ),
                (
                    "news",
                    models.ForeignKey(
                        related_name="dates", to="com.News", verbose_name="news_date"
                    ),
                ),
            ],
        ),
    ]
