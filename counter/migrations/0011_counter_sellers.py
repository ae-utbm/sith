# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscription', '0002_auto_20160718_1805'),
        ('counter', '0010_auto_20160728_1820'),
    ]

    operations = [
        migrations.AddField(
            model_name='counter',
            name='sellers',
            field=models.ManyToManyField(verbose_name='sellers', to='subscription.Subscriber', related_name='counters', blank=True),
        ),
    ]
