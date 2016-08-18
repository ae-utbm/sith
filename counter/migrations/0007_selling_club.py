# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('club', '0004_auto_20160813_1551'),
        ('counter', '0006_auto_20160817_2253'),
    ]

    operations = [
        migrations.AddField(
            model_name='selling',
            name='club',
            field=models.ForeignKey(default=1, related_name='sellings', to='club.Club'),
            preserve_default=False,
        ),
    ]
