# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0018_auto_20161224_0211"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Candidature",
            fields=[
                (
                    "id",
                    models.AutoField(
                        primary_key=True,
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                    ),
                ),
                (
                    "program",
                    models.TextField(null=True, verbose_name="description", blank=True),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Election",
            fields=[
                (
                    "id",
                    models.AutoField(
                        primary_key=True,
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                    ),
                ),
                ("title", models.CharField(max_length=255, verbose_name="title")),
                (
                    "description",
                    models.TextField(null=True, verbose_name="description", blank=True),
                ),
                (
                    "start_candidature",
                    models.DateTimeField(verbose_name="start candidature"),
                ),
                (
                    "end_candidature",
                    models.DateTimeField(verbose_name="end candidature"),
                ),
                ("start_date", models.DateTimeField(verbose_name="start date")),
                ("end_date", models.DateTimeField(verbose_name="end date")),
                (
                    "candidature_groups",
                    models.ManyToManyField(
                        related_name="candidate_elections",
                        verbose_name="candidature groups",
                        blank=True,
                        to="core.Group",
                    ),
                ),
                (
                    "edit_groups",
                    models.ManyToManyField(
                        related_name="editable_elections",
                        verbose_name="edit groups",
                        blank=True,
                        to="core.Group",
                    ),
                ),
                (
                    "view_groups",
                    models.ManyToManyField(
                        related_name="viewable_elections",
                        verbose_name="view groups",
                        blank=True,
                        to="core.Group",
                    ),
                ),
                (
                    "vote_groups",
                    models.ManyToManyField(
                        related_name="votable_elections",
                        verbose_name="vote groups",
                        blank=True,
                        to="core.Group",
                    ),
                ),
                (
                    "voters",
                    models.ManyToManyField(
                        related_name="voted_elections",
                        verbose_name="voters",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ElectionList",
            fields=[
                (
                    "id",
                    models.AutoField(
                        primary_key=True,
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                    ),
                ),
                ("title", models.CharField(max_length=255, verbose_name="title")),
                (
                    "election",
                    models.ForeignKey(
                        verbose_name="election",
                        to="election.Election",
                        related_name="election_lists",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Role",
            fields=[
                (
                    "id",
                    models.AutoField(
                        primary_key=True,
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                    ),
                ),
                ("title", models.CharField(max_length=255, verbose_name="title")),
                (
                    "description",
                    models.TextField(null=True, verbose_name="description", blank=True),
                ),
                (
                    "max_choice",
                    models.IntegerField(verbose_name="max choice", default=1),
                ),
                (
                    "election",
                    models.ForeignKey(
                        verbose_name="election",
                        to="election.Election",
                        related_name="roles",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Vote",
            fields=[
                (
                    "id",
                    models.AutoField(
                        primary_key=True,
                        verbose_name="ID",
                        serialize=False,
                        auto_created=True,
                    ),
                ),
                (
                    "candidature",
                    models.ManyToManyField(
                        related_name="votes",
                        verbose_name="candidature",
                        to="election.Candidature",
                    ),
                ),
                (
                    "role",
                    models.ForeignKey(
                        verbose_name="role", to="election.Role", related_name="votes"
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="candidature",
            name="election_list",
            field=models.ForeignKey(
                verbose_name="election list",
                to="election.ElectionList",
                related_name="candidatures",
            ),
        ),
        migrations.AddField(
            model_name="candidature",
            name="role",
            field=models.ForeignKey(
                verbose_name="role", to="election.Role", related_name="candidatures"
            ),
        ),
        migrations.AddField(
            model_name="candidature",
            name="user",
            field=models.ForeignKey(
                verbose_name="user",
                to=settings.AUTH_USER_MODEL,
                related_name="candidates",
                blank=True,
            ),
        ),
    ]
