# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('com', '0003_auto_20170103_1341'),
    ]

    operations = [
        migrations.AlterField(
            model_name='weekmail',
            name='title',
            field=models.CharField(verbose_name='title', max_length=64, blank=True),
        ),
        migrations.AlterField(
            model_name='weekmailarticle',
            name='weekmail',
            field=models.ForeignKey(related_name='articles', to='com.Weekmail', verbose_name='weekmail', null=True),
        ),
    ]
