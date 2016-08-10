# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0016_auto_20160807_2000'),
    ]

    operations = [
        migrations.AlterField(
            model_name='operation',
            name='invoice',
            field=models.ForeignKey(blank=True, related_name='operations', to='core.SithFile', null=True, verbose_name='invoice'),
        ),
    ]
