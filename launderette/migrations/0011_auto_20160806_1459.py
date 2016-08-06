# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('launderette', '0010_auto_20160806_1242'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='token',
            options={'ordering': ['type', 'name'], 'verbose_name': 'Token'},
        ),
    ]
