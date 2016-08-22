# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('counter', '0019_auto_20160820_2053'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='buying_groups',
            field=models.ManyToManyField(to='core.Group', related_name='products', verbose_name='buying groups'),
        ),
    ]
