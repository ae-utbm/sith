# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='description',
            field=models.TextField(verbose_name='description', blank=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='icon',
            field=models.ImageField(null=True, upload_to='products', blank=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='product_type',
            field=models.ForeignKey(to='accounting.ProductType', null=True, blank=True, related_name='products'),
        ),
        migrations.AlterField(
            model_name='producttype',
            name='description',
            field=models.TextField(verbose_name='description', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='producttype',
            name='icon',
            field=models.ImageField(null=True, upload_to='products', blank=True),
        ),
    ]
