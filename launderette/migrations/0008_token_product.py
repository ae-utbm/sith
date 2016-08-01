# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('counter', '0011_counter_sellers'),
        ('launderette', '0007_auto_20160801_1929'),
    ]

    operations = [
        migrations.AddField(
            model_name='token',
            name='product',
            field=models.ForeignKey(related_name='tokens', to='counter.Product', default=1, verbose_name='product'),
            preserve_default=False,
        ),
    ]
