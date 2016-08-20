# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_auto_20160813_0522'),
        ('counter', '0017_auto_20160820_2047'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='buying_group',
        ),
        migrations.AddField(
            model_name='product',
            name='buying_group',
            field=models.ManyToManyField(related_name='products', to='core.Group', verbose_name='buying group'),
        ),
    ]
