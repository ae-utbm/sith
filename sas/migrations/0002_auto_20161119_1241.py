# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("sas", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="PeoplePictureRelation",
            fields=[
                (
                    "id",
                    models.AutoField(
                        primary_key=True,
                        verbose_name="ID",
                        auto_created=True,
                        serialize=False,
                    ),
                ),
                (
                    "picture",
                    models.ForeignKey(
                        related_name="people", to="sas.Picture", verbose_name="picture"
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        related_name="pictures",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="user",
                    ),
                ),
            ],
        ),
        migrations.AlterUniqueTogether(
            name="peoplepicturerelation", unique_together=set([("user", "picture")])
        ),
    ]
