# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('launderette', '0001_squashed_0006_auto_20160729_0050'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='slot',
            options={'verbose_name': 'Slot'},
        ),
    ]
