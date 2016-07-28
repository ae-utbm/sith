# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('counter', '0009_auto_20160721_1902'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='counter',
            options={'verbose_name': 'counter'},
        ),
        migrations.AlterModelOptions(
            name='permanency',
            options={'verbose_name': 'permanency'},
        ),
        migrations.AlterModelOptions(
            name='product',
            options={'verbose_name': 'product'},
        ),
        migrations.AlterModelOptions(
            name='producttype',
            options={'verbose_name': 'product type'},
        ),
        migrations.AlterModelOptions(
            name='refilling',
            options={'verbose_name': 'refilling'},
        ),
        migrations.AlterModelOptions(
            name='selling',
            options={'verbose_name': 'selling'},
        ),
    ]
