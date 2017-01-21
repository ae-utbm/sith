# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forum', '0003_auto_20170121_0311'),
    ]

    operations = [
        migrations.AddField(
            model_name='forumtopic',
            name='description',
            field=models.CharField(max_length=256, verbose_name='description', default=''),
        ),
    ]
