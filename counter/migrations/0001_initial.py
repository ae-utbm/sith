# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import accounting.models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('club', '0001_initial'),
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Counter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('name', models.CharField(max_length=30, verbose_name='name')),
                ('type', models.CharField(choices=[('BAR', 'Bar'), ('OFFICE', 'Office')], max_length=255, verbose_name='subscription type')),
                ('club', models.ForeignKey(to='club.Club', related_name='counters')),
                ('edit_groups', models.ManyToManyField(related_name='editable_counters', to='core.Group', blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL, primary_key=True, serialize=False)),
                ('account_id', models.CharField(unique=True, max_length=10, verbose_name='account id')),
            ],
            options={
                'verbose_name_plural': 'customers',
                'verbose_name': 'customer',
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('name', models.CharField(max_length=30, verbose_name='name')),
                ('description', models.TextField(blank=True, verbose_name='description')),
                ('code', models.CharField(max_length=10, verbose_name='code')),
                ('purchase_price', accounting.models.CurrencyField(max_digits=12, decimal_places=2, verbose_name='purchase price')),
                ('selling_price', accounting.models.CurrencyField(max_digits=12, decimal_places=2, verbose_name='selling price')),
                ('special_selling_price', accounting.models.CurrencyField(max_digits=12, decimal_places=2, verbose_name='special selling price')),
                ('icon', models.ImageField(blank=True, upload_to='products', null=True)),
                ('club', models.ForeignKey(to='club.Club', related_name='products')),
            ],
        ),
        migrations.CreateModel(
            name='ProductType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('name', models.CharField(max_length=30, verbose_name='name')),
                ('description', models.TextField(blank=True, verbose_name='description', null=True)),
                ('icon', models.ImageField(blank=True, upload_to='products', null=True)),
            ],
        ),
        migrations.AddField(
            model_name='product',
            name='product_type',
            field=models.ForeignKey(to='counter.ProductType', related_name='products', null=True, blank=True),
        ),
        migrations.AddField(
            model_name='counter',
            name='products',
            field=models.ManyToManyField(related_name='counters', to='counter.Product', blank=True),
        ),
        migrations.AddField(
            model_name='counter',
            name='view_groups',
            field=models.ManyToManyField(related_name='viewable_counters', to='core.Group', blank=True),
        ),
    ]
