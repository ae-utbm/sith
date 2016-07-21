# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import accounting.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('counter', '0009_auto_20160721_1902'),
    ]

    operations = [
        migrations.CreateModel(
            name='Basket',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('date', models.DateTimeField(auto_now=True, verbose_name='date')),
                ('user', models.ForeignKey(verbose_name='user', related_name='baskets', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='BasketItem',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('product_name', models.CharField(max_length=255, verbose_name='product name')),
                ('product_unit_price', accounting.models.CurrencyField(max_digits=12, decimal_places=2, verbose_name='unit price')),
                ('quantity', models.IntegerField(verbose_name='quantity')),
                ('basket', models.ForeignKey(verbose_name='basket', related_name='items', to='eboutic.Basket')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('date', models.DateTimeField(auto_now=True, verbose_name='date')),
                ('payment_method', models.CharField(max_length=20, choices=[('CREDIT_CARD', 'Credit card'), ('SITH_ACCOUNT', 'Sith account')], verbose_name='payment method')),
                ('products', models.ManyToManyField(related_name='invoices', to='counter.Product', blank=True, verbose_name='products')),
                ('user', models.ForeignKey(verbose_name='user', related_name='invoices', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='InvoiceItem',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('product_name', models.CharField(max_length=255, verbose_name='product name')),
                ('product_unit_price', accounting.models.CurrencyField(max_digits=12, decimal_places=2, verbose_name='unit price')),
                ('quantity', models.IntegerField(verbose_name='quantity')),
                ('invoice', models.ForeignKey(verbose_name='invoice', related_name='items', to='eboutic.Invoice')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Eboutic',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('counter.counter',),
        ),
    ]
