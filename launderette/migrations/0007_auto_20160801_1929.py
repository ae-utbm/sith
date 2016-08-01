# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('launderette', '0006_auto_20160801_1928'),
    ]

    operations = [
        migrations.AlterField(
            model_name='token',
            name='user',
            field=models.ForeignKey(verbose_name='user', related_name='tokens', blank=True, null=True, to='subscription.Subscriber'),
        ),
    ]
