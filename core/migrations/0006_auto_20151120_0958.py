# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_page_title'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='page',
            name='id',
        ),
        migrations.AlterField(
            model_name='page',
            name='full_name',
            field=models.CharField(primary_key=True, max_length=255, serialize=False, verbose_name='full name'),
        ),
    ]
