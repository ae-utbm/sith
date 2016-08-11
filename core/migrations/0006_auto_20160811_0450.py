# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_auto_20160811_0319'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='dpt_option',
            field=models.CharField(verbose_name='dpt option', null=True, max_length=32, blank=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='forum_signature',
            field=models.TextField(verbose_name='forum signature', null=True, max_length=256, blank=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='quote',
            field=models.CharField(verbose_name='quote', null=True, max_length=64, blank=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='school',
            field=models.CharField(verbose_name='school', null=True, max_length=32, blank=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='semester',
            field=models.CharField(verbose_name='semester', null=True, max_length=5, blank=True),
        ),
    ]
