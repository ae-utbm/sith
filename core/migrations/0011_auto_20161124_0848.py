# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
import core.models


class Migration(migrations.Migration):

    dependencies = [("core", "0010_sithfile_is_in_sas")]

    operations = [
        migrations.AlterField(
            model_name="sithfile",
            name="compressed",
            field=models.FileField(
                verbose_name="compressed file",
                upload_to=core.models.get_compressed_directory,
                null=True,
                blank=True,
                max_length=256,
            ),
        ),
        migrations.AlterField(
            model_name="sithfile",
            name="date",
            field=models.DateTimeField(
                verbose_name="date", default=django.utils.timezone.now
            ),
        ),
        migrations.AlterField(
            model_name="sithfile",
            name="file",
            field=models.FileField(
                verbose_name="file",
                upload_to=core.models.get_directory,
                null=True,
                blank=True,
                max_length=256,
            ),
        ),
        migrations.AlterField(
            model_name="sithfile",
            name="thumbnail",
            field=models.FileField(
                verbose_name="thumbnail",
                upload_to=core.models.get_thumbnail_directory,
                null=True,
                blank=True,
                max_length=256,
            ),
        ),
    ]
