# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('counter', '0004_auto_20160717_0933'),
    ]

    operations = [
        migrations.AlterField(
            model_name='refilling',
            name='customer',
            field=models.ForeignKey(to='counter.Customer', related_name='refillings'),
        ),
        migrations.AlterField(
            model_name='refilling',
            name='operator',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='refillings_as_operator'),
        ),
        migrations.AlterField(
            model_name='selling',
            name='customer',
            field=models.ForeignKey(to='counter.Customer', related_name='sellings'),
        ),
        migrations.AlterField(
            model_name='selling',
            name='seller',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='sellings_as_operator'),
        ),
    ]
