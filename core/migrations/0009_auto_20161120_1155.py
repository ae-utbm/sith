# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import core.models


class Migration(migrations.Migration):

    dependencies = [("core", "0008_sithfile_asked_for_removal")]

    operations = [
        migrations.AddField(
            model_name="sithfile",
            name="compressed",
            field=models.FileField(
                upload_to=core.models.get_compressed_directory,
                null=True,
                verbose_name="compressed file",
                blank=True,
            ),
        ),
        migrations.AddField(
            model_name="sithfile",
            name="thumbnail",
            field=models.FileField(
                upload_to=core.models.get_thumbnail_directory,
                null=True,
                verbose_name="thumbnail",
                blank=True,
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="home",
            field=models.OneToOneField(
                verbose_name="home",
                related_name="home_of",
                on_delete=django.db.models.deletion.SET_NULL,
                null=True,
                to="core.SithFile",
                blank=True,
            ),
        ),
    ]
