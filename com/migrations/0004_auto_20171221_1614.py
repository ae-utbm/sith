# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ("club", "0010_auto_20170912_2028"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("com", "0003_auto_20170115_2300"),
    ]

    operations = [
        migrations.CreateModel(
            name="Poster",
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
                    "name",
                    models.CharField(verbose_name="name", max_length=128, default=""),
                ),
                (
                    "file",
                    models.ImageField(verbose_name="file", upload_to="com/posters"),
                ),
                ("date_begin", models.DateTimeField(default=django.utils.timezone.now)),
                ("date_end", models.DateTimeField(blank=True, null=True)),
                (
                    "display_time",
                    models.IntegerField(verbose_name="display time", default=30),
                ),
                (
                    "is_moderated",
                    models.BooleanField(verbose_name="is moderated", default=False),
                ),
                (
                    "club",
                    models.ForeignKey(
                        verbose_name="club", related_name="posters", to="club.Club"
                    ),
                ),
                (
                    "moderator",
                    models.ForeignKey(
                        verbose_name="moderator",
                        blank=True,
                        null=True,
                        related_name="moderated_posters",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Screen",
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
                ("name", models.CharField(verbose_name="name", max_length=128)),
            ],
        ),
        migrations.AddField(
            model_name="poster",
            name="screens",
            field=models.ManyToManyField(related_name="posters", to="com.Screen"),
        ),
    ]
