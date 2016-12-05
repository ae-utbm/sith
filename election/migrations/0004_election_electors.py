# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscription', '0003_auto_20160902_1914'),
        ('election', '0003_auto_20161205_2235'),
    ]

    operations = [
        migrations.AddField(
            model_name='election',
            name='electors',
            field=models.ManyToManyField(verbose_name='electors', related_name='election', blank=True, to='subscription.Subscriber'),
        ),
    ]
