# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eboutic', '0003_auto_20160726_1708'),
    ]

    operations = [
        migrations.AddField(
            model_name='basketitem',
            name='product_id',
            field=models.IntegerField(verbose_name='product id', default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='invoiceitem',
            name='product_id',
            field=models.IntegerField(verbose_name='product id', default=0),
            preserve_default=False,
        ),
    ]
