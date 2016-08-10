# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('counter', '0001_initial'),
        ('core', '0001_initial'),
        ('subscription', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='counter',
            name='sellers',
            field=models.ManyToManyField(verbose_name='sellers', to='subscription.Subscriber', related_name='counters', blank=True),
        ),
        migrations.AddField(
            model_name='counter',
            name='view_groups',
            field=models.ManyToManyField(to='core.Group', related_name='viewable_counters', blank=True),
        ),
    ]
