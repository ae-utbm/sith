# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.contrib.auth.models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('subscription_type', models.CharField(verbose_name='subscription type', max_length=255, choices=[('cursus-branche', 'Branch cursus'), ('cursus-tronc-commun', 'Common core cursus'), ('deux-semestres', 'Two semesters'), ('un-semestre', 'One semester')])),
                ('subscription_start', models.DateField(verbose_name='subscription start')),
                ('subscription_end', models.DateField(verbose_name='subscription end')),
                ('payment_method', models.CharField(verbose_name='payment method', max_length=255, choices=[('CHEQUE', 'Check'), ('CASH', 'Cash'), ('OTHER', 'Other')])),
                ('location', models.CharField(verbose_name='location', max_length=20, choices=[('BELFORT', 'Belfort'), ('SEVENANS', 'Sevenans'), ('MONTBELIARD', 'Montbéliard')])),
            ],
            options={
                'ordering': ['subscription_start'],
            },
        ),
        migrations.CreateModel(
            name='Subscriber',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('core.user',),
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.AddField(
            model_name='subscription',
            name='member',
            field=models.ForeignKey(related_name='subscriptions', to='subscription.Subscriber'),
        ),
    ]
