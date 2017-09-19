# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('club', '0010_auto_20170912_2028'),
    ]

    operations = [
        migrations.AddField(
            model_name='club',
            name='short_description',
            field=models.CharField(max_length=1000, verbose_name='short description', blank=True),
        ),
    ]
