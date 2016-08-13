# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('club', '0003_auto_20160813_1448'),
    ]

    operations = [
        migrations.AlterField(
            model_name='membership',
            name='description',
            field=models.CharField(verbose_name='description', blank=True, max_length=128),
        ),
    ]
