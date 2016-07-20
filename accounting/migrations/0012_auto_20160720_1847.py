# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0011_auto_20160718_1805'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='operation',
            options={'ordering': ['-number']},
        ),
        migrations.AddField(
            model_name='operation',
            name='number',
            field=models.IntegerField(default=1, verbose_name='number'),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='operation',
            unique_together=set([('number', 'journal')]),
        ),
    ]
