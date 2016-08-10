# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import accounting.models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Basket',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('date', models.DateTimeField(verbose_name='date', auto_now=True)),
                ('user', models.ForeignKey(verbose_name='user', related_name='baskets', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='BasketItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('product_id', models.IntegerField(verbose_name='product id')),
                ('product_name', models.CharField(verbose_name='product name', max_length=255)),
                ('type', models.CharField(verbose_name='product type', max_length=255)),
                ('product_unit_price', accounting.models.CurrencyField(verbose_name='unit price', decimal_places=2, max_digits=12)),
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
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('date', models.DateTimeField(verbose_name='date', auto_now=True)),
                ('payment_method', models.CharField(verbose_name='payment method', max_length=20, choices=[('CREDIT_CARD', 'Credit card'), ('SITH_ACCOUNT', 'Sith account')])),
                ('validated', models.BooleanField(default=False, verbose_name='validated')),
                ('user', models.ForeignKey(verbose_name='user', related_name='invoices', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='InvoiceItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('product_id', models.IntegerField(verbose_name='product id')),
                ('product_name', models.CharField(verbose_name='product name', max_length=255)),
                ('type', models.CharField(verbose_name='product type', max_length=255)),
                ('product_unit_price', accounting.models.CurrencyField(verbose_name='unit price', decimal_places=2, max_digits=12)),
                ('quantity', models.IntegerField(verbose_name='quantity')),
                ('invoice', models.ForeignKey(verbose_name='invoice', related_name='items', to='eboutic.Invoice')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
