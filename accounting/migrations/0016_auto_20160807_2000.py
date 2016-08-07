# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0015_auto_20160807_1959'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='accountingtype',
            options={'verbose_name': 'accounting type'},
        ),
    ]
