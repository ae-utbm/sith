# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import accounting.models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('counter', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Refilling',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('amount', accounting.models.CurrencyField(verbose_name='amount', decimal_places=2, max_digits=12)),
                ('date', models.DateTimeField(verbose_name='date', auto_now=True)),
                ('payment_method', models.CharField(verbose_name='payment method', max_length=255, choices=[('cheque', 'Chèque'), ('cash', 'Espèce')])),
                ('counter', models.ForeignKey(to='counter.Counter', related_name='refillings')),
                ('customer', models.ForeignKey(to='counter.Customer', related_name='refill_customers')),
                ('operator', models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='refill_operators')),
            ],
        ),
        migrations.CreateModel(
            name='Selling',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('unit_price', accounting.models.CurrencyField(verbose_name='unit price', decimal_places=2, max_digits=12)),
                ('quantity', models.IntegerField(verbose_name='quantity')),
                ('date', models.DateTimeField(verbose_name='date', auto_now=True)),
                ('counter', models.ForeignKey(to='counter.Counter', related_name='sellings')),
                ('customer', models.ForeignKey(to='counter.Customer', related_name='customers')),
                ('product', models.ForeignKey(to='counter.Product', related_name='sellings')),
                ('seller', models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='sellers')),
            ],
        ),
    ]
