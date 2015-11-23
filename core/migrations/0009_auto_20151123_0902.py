# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_auto_20151122_1717'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='page',
            name='id',
        ),
        migrations.AlterField(
            model_name='page',
            name='name',
            field=models.CharField(verbose_name='page name', max_length=30, serialize=False, primary_key=True),
        ),
    ]
