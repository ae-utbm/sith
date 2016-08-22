# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_auto_20160813_0522'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_subscriber_viewable',
            field=models.BooleanField(default=True, verbose_name='is subscriber viewable'),
        ),
    ]
