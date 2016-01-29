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
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('subscription_type', models.CharField(choices=[('cursus-branche', 'Cursus Branche'), ('cursus-tronc-commun', 'Cursus Tronc Commun'), ('deux-semestres', 'Deux semestres'), ('un-semestre', 'Un semestre')], max_length=255, verbose_name='subscription type')),
                ('subscription_start', models.DateField(verbose_name='subscription start')),
                ('subscription_end', models.DateField(verbose_name='subscription end')),
                ('payment_method', models.CharField(choices=[('cheque', 'Chèque'), ('cash', 'Espèce'), ('other', 'Autre')], max_length=255, verbose_name='payment method')),
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
