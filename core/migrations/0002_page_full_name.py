# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='page',
            name='full_name',
            field=models.CharField(blank=True, verbose_name='page name', max_length=255),
        ),
    ]
