# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forum', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='forumtopic',
            name='title',
            field=models.CharField(verbose_name='title', max_length=64, default=''),
        ),
    ]
