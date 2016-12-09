# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_notification'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='notification',
            name='text',
        ),
        migrations.AddField(
            model_name='notification',
            name='param',
            field=models.CharField(verbose_name='param', default='', max_length=128),
        ),
        migrations.AddField(
            model_name='notification',
            name='viewed',
            field=models.BooleanField(verbose_name='viewed', default=False),
        ),
    ]
