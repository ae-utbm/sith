# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('launderette', '0005_auto_20160801_1634'),
    ]

    operations = [
        migrations.AlterField(
            model_name='token',
            name='borrow_date',
            field=models.DateTimeField(blank=True, verbose_name='borrow date', null=True),
        ),
        migrations.AlterField(
            model_name='token',
            name='user',
            field=models.ForeignKey(blank=True, to='subscription.Subscriber', related_name='tokens', verbose_name='user'),
        ),
    ]
