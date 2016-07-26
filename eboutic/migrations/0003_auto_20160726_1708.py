# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eboutic', '0002_auto_20160722_0100'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Eboutic',
        ),
        migrations.AddField(
            model_name='basketitem',
            name='type',
            field=models.CharField(default='GUY', verbose_name='product type', max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='invoiceitem',
            name='type',
            field=models.CharField(default='GUY', verbose_name='product type', max_length=255),
            preserve_default=False,
        ),
    ]
