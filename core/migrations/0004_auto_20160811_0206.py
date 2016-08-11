# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_auto_20160810_1949'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='nick_name',
            field=models.CharField(verbose_name='nick name', max_length=30, blank=True),
        ),
    ]
