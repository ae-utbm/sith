# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_auto_20151123_1002'),
    ]

    operations = [
        migrations.AlterField(
            model_name='page',
            name='full_name',
            field=models.CharField(verbose_name='page full name', primary_key=True, serialize=False, max_length=30),
        ),
        migrations.AlterField(
            model_name='page',
            name='parent',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, to='core.Page', related_name='children', null=True),
        ),
    ]
