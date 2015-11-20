# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_auto_20151120_0958'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='page',
            name='full_name',
        ),
        migrations.AddField(
            model_name='page',
            name='id',
            field=models.AutoField(default=0, auto_created=True, verbose_name='ID', primary_key=True, serialize=False),
            preserve_default=False,
        ),
    ]
