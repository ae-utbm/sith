# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('counter', '0012_auto_20170515_2202'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='recorded_products',
            field=models.IntegerField(verbose_name='recorded items', default=0),
        ),
    ]
