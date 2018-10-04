# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("club", "0001_initial"),
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="membership",
            name="user",
            field=models.ForeignKey(
                verbose_name="user",
                to=settings.AUTH_USER_MODEL,
                related_name="membership",
            ),
        ),
        migrations.AddField(
            model_name="club",
            name="edit_groups",
            field=models.ManyToManyField(
                to="core.Group", blank=True, related_name="editable_club"
            ),
        ),
        migrations.AddField(
            model_name="club",
            name="home",
            field=models.OneToOneField(
                blank=True,
                null=True,
                related_name="home_of_club",
                verbose_name="home",
                to="core.SithFile",
            ),
        ),
        migrations.AddField(
            model_name="club",
            name="owner_group",
            field=models.ForeignKey(
                default=1, to="core.Group", related_name="owned_club"
            ),
        ),
        migrations.AddField(
            model_name="club",
            name="parent",
            field=models.ForeignKey(
                null=True, to="club.Club", related_name="children", blank=True
            ),
        ),
        migrations.AddField(
            model_name="club",
            name="view_groups",
            field=models.ManyToManyField(
                to="core.Group", blank=True, related_name="viewable_club"
            ),
        ),
    ]
