# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('counter', '0012_auto_20160801_2016'),
    ]

    operations = [
        migrations.AlterField(
            model_name='selling',
            name='product',
            field=models.ForeignKey(to='counter.Product', null=True, related_name='sellings', blank=True),
        ),
    ]
