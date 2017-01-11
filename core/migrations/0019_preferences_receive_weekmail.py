# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0018_auto_20161224_0211'),
    ]

    operations = [
        migrations.AddField(
            model_name='preferences',
            name='receive_weekmail',
            field=models.BooleanField(verbose_name='define if we want to receive the weekmail', default=False, help_text='Do you want to receive the weekmail'),
        ),
    ]
