# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.utils.timezone import utc
from django.conf import settings
import django.utils.timezone
import datetime


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("club", "0006_auto_20161229_0040"),
        ("core", "0019_preferences_receive_weekmail"),
    ]

    operations = [
        migrations.CreateModel(
            name="Forum",
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
                    "description",
                    models.CharField(
                        max_length=256, verbose_name="description", default=""
                    ),
                ),
                (
                    "is_category",
                    models.BooleanField(verbose_name="is a category", default=False),
                ),
                (
                    "edit_groups",
                    models.ManyToManyField(
                        related_name="editable_forums",
                        to="core.Group",
                        blank=True,
                        default=[4],
                    ),
                ),
                (
                    "owner_club",
                    models.ForeignKey(
                        to="club.Club",
                        verbose_name="owner club",
                        related_name="owned_forums",
                        default=1,
                    ),
                ),
                (
                    "parent",
                    models.ForeignKey(
                        to="forum.Forum", null=True, related_name="children", blank=True
                    ),
                ),
                (
                    "view_groups",
                    models.ManyToManyField(
                        related_name="viewable_forums",
                        to="core.Group",
                        blank=True,
                        default=[2],
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ForumMessage",
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
                    "title",
                    models.CharField(
                        max_length=64, blank=True, verbose_name="title", default=""
                    ),
                ),
                ("message", models.TextField(verbose_name="message", default="")),
                (
                    "date",
                    models.DateTimeField(
                        verbose_name="date", default=django.utils.timezone.now
                    ),
                ),
                (
                    "author",
                    models.ForeignKey(
                        related_name="forum_messages", to=settings.AUTH_USER_MODEL
                    ),
                ),
                (
                    "readers",
                    models.ManyToManyField(
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="readers",
                        related_name="read_messages",
                    ),
                ),
            ],
            options={"ordering": ["id"]},
        ),
        migrations.CreateModel(
            name="ForumMessageMeta",
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
                    "date",
                    models.DateTimeField(
                        verbose_name="date", default=django.utils.timezone.now
                    ),
                ),
                (
                    "action",
                    models.CharField(
                        max_length=16,
                        choices=[
                            ("EDIT", "Message edited by"),
                            ("DELETE", "Message deleted by"),
                            ("UNDELETE", "Message undeleted by"),
                        ],
                        verbose_name="action",
                    ),
                ),
                (
                    "message",
                    models.ForeignKey(related_name="metas", to="forum.ForumMessage"),
                ),
                (
                    "user",
                    models.ForeignKey(
                        related_name="forum_message_metas", to=settings.AUTH_USER_MODEL
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ForumTopic",
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
                    "description",
                    models.CharField(
                        max_length=256, verbose_name="description", default=""
                    ),
                ),
                (
                    "author",
                    models.ForeignKey(
                        related_name="forum_topics", to=settings.AUTH_USER_MODEL
                    ),
                ),
                ("forum", models.ForeignKey(related_name="topics", to="forum.Forum")),
            ],
            options={"ordering": ["-id"]},
        ),
        migrations.CreateModel(
            name="ForumUserInfo",
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
                    "last_read_date",
                    models.DateTimeField(
                        verbose_name="last read date",
                        default=datetime.datetime(1999, 1, 1, 0, 0, tzinfo=utc),
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        to=settings.AUTH_USER_MODEL, related_name="_forum_infos"
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="forummessage",
            name="topic",
            field=models.ForeignKey(related_name="messages", to="forum.ForumTopic"),
        ),
    ]
