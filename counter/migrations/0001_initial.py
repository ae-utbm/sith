# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import accounting.models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0001_initial'),
        ('club', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Counter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('name', models.CharField(verbose_name='name', max_length=30)),
                ('type', models.CharField(verbose_name='subscription type', max_length=255, choices=[('BAR', 'Bar'), ('OFFICE', 'Office'), ('EBOUTIC', 'Eboutic')])),
                ('club', models.ForeignKey(related_name='counters', to='club.Club')),
                ('edit_groups', models.ManyToManyField(to='core.Group', related_name='editable_counters', blank=True)),
            ],
            options={
                'verbose_name': 'counter',
            },
        ),
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('user', models.OneToOneField(primary_key=True, serialize=False, to=settings.AUTH_USER_MODEL)),
                ('account_id', models.CharField(verbose_name='account id', unique=True, max_length=10)),
                ('amount', accounting.models.CurrencyField(verbose_name='amount', decimal_places=2, max_digits=12)),
            ],
            options={
                'verbose_name': 'customer',
                'verbose_name_plural': 'customers',
                'ordering': ['account_id'],
            },
        ),
        migrations.CreateModel(
            name='Permanency',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('start', models.DateTimeField(verbose_name='start date')),
                ('end', models.DateTimeField(verbose_name='end date')),
                ('counter', models.ForeignKey(related_name='permanencies', to='counter.Counter')),
                ('user', models.ForeignKey(related_name='permanencies', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'permanency',
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('name', models.CharField(verbose_name='name', max_length=30)),
                ('description', models.TextField(verbose_name='description', blank=True)),
                ('code', models.CharField(verbose_name='code', max_length=10)),
                ('purchase_price', accounting.models.CurrencyField(verbose_name='purchase price', decimal_places=2, max_digits=12)),
                ('selling_price', accounting.models.CurrencyField(verbose_name='selling price', decimal_places=2, max_digits=12)),
                ('special_selling_price', accounting.models.CurrencyField(verbose_name='special selling price', decimal_places=2, max_digits=12)),
                ('icon', models.ImageField(upload_to='products', null=True, blank=True)),
                ('club', models.ForeignKey(related_name='products', to='club.Club')),
            ],
            options={
                'verbose_name': 'product',
            },
        ),
        migrations.CreateModel(
            name='ProductType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('name', models.CharField(verbose_name='name', max_length=30)),
                ('description', models.TextField(verbose_name='description', null=True, blank=True)),
                ('icon', models.ImageField(upload_to='products', null=True, blank=True)),
            ],
            options={
                'verbose_name': 'product type',
            },
        ),
        migrations.CreateModel(
            name='Refilling',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('amount', accounting.models.CurrencyField(verbose_name='amount', decimal_places=2, max_digits=12)),
                ('date', models.DateTimeField(verbose_name='date', auto_now=True)),
                ('payment_method', models.CharField(default='cash', verbose_name='payment method', max_length=255, choices=[('CHEQUE', 'Check'), ('CASH', 'Cash')])),
                ('bank', models.CharField(default='other', verbose_name='bank', max_length=255, choices=[('OTHER', 'Autre'), ('LA-POSTE', 'La Poste'), ('CREDIT-AGRICOLE', 'Credit Agricole'), ('CREDIT-MUTUEL', 'Credit Mutuel')])),
                ('is_validated', models.BooleanField(default=False, verbose_name='is validated')),
                ('counter', models.ForeignKey(related_name='refillings', to='counter.Counter')),
                ('customer', models.ForeignKey(related_name='refillings', to='counter.Customer')),
                ('operator', models.ForeignKey(related_name='refillings_as_operator', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'refilling',
            },
        ),
        migrations.CreateModel(
            name='Selling',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('label', models.CharField(verbose_name='label', max_length=30)),
                ('unit_price', accounting.models.CurrencyField(verbose_name='unit price', decimal_places=2, max_digits=12)),
                ('quantity', models.IntegerField(verbose_name='quantity')),
                ('date', models.DateTimeField(verbose_name='date', auto_now=True)),
                ('is_validated', models.BooleanField(default=False, verbose_name='is validated')),
                ('counter', models.ForeignKey(related_name='sellings', to='counter.Counter')),
                ('customer', models.ForeignKey(related_name='buyings', to='counter.Customer')),
                ('product', models.ForeignKey(blank=True, null=True, to='counter.Product', related_name='sellings')),
                ('seller', models.ForeignKey(related_name='sellings_as_operator', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'selling',
            },
        ),
        migrations.AddField(
            model_name='product',
            name='product_type',
            field=models.ForeignKey(blank=True, null=True, to='counter.ProductType', related_name='products'),
        ),
        migrations.AddField(
            model_name='counter',
            name='products',
            field=models.ManyToManyField(to='counter.Product', related_name='counters', blank=True),
        ),
    ]
