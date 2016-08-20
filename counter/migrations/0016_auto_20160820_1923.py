# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_auto_20160813_0522'),
        ('counter', '0015_auto_20160820_0158'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='buying_group',
            field=models.ForeignKey(blank=True, on_delete=django.db.models.deletion.SET_NULL, verbose_name='buying group', related_name='products', to='core.Group', null=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='club',
            field=models.ForeignKey(verbose_name='club', to='club.Club', related_name='products'),
        ),
        migrations.AlterField(
            model_name='product',
            name='icon',
            field=models.ImageField(blank=True, null=True, upload_to='products', verbose_name='icon'),
        ),
        migrations.AlterField(
            model_name='product',
            name='product_type',
            field=models.ForeignKey(blank=True, on_delete=django.db.models.deletion.SET_NULL, verbose_name='parent product', related_name='children_products', to='counter.Product', null=True),
        ),
    ]
