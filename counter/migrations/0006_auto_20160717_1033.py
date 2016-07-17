# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('counter', '0005_auto_20160717_1029'),
    ]

    operations = [
        migrations.AlterField(
            model_name='selling',
            name='customer',
            field=models.ForeignKey(to='counter.Customer', related_name='buyings'),
        ),
    ]
