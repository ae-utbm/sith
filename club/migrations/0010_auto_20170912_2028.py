# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

from club.models import Club
from core.operations import PsqlRunOnly


def generate_club_pages(apps, schema_editor):
    def recursive_generate_club_page(club):
        club.make_page()
        for child in Club.objects.filter(parent=club).all():
            recursive_generate_club_page(child)

    for club in Club.objects.filter(parent=None).all():
        recursive_generate_club_page(club)


class Migration(migrations.Migration):

    dependencies = [("core", "0024_auto_20170906_1317"), ("club", "0010_club_logo")]

    operations = [
        migrations.AddField(
            model_name="club",
            name="is_active",
            field=models.BooleanField(default=True, verbose_name="is active"),
        ),
        migrations.AddField(
            model_name="club",
            name="page",
            field=models.OneToOneField(
                related_name="club", blank=True, null=True, to="core.Page"
            ),
        ),
        migrations.AddField(
            model_name="club",
            name="short_description",
            field=models.CharField(
                verbose_name="short description",
                max_length=1000,
                default="",
                blank=True,
                null=True,
            ),
        ),
        PsqlRunOnly(
            "SET CONSTRAINTS ALL IMMEDIATE", reverse_sql=migrations.RunSQL.noop
        ),
        migrations.RunPython(generate_club_pages),
        PsqlRunOnly(
            migrations.RunSQL.noop, reverse_sql="SET CONSTRAINTS ALL IMMEDIATE"
        ),
    ]
