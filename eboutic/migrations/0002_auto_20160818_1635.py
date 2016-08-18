# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eboutic', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='basketitem',
            name='type',
        ),
        migrations.RemoveField(
            model_name='invoiceitem',
            name='type',
        ),
        migrations.AddField(
            model_name='basketitem',
            name='type_id',
            field=models.IntegerField(default=1, verbose_name='product type id'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='invoiceitem',
            name='type_id',
            field=models.IntegerField(default=1, verbose_name='product type id'),
            preserve_default=False,
        ),
    ]
