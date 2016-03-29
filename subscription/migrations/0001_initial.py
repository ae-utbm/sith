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
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('subscription_type', models.CharField(max_length=255, verbose_name='subscription type', choices=[('cursus-branche', 'Cursus Branche'), ('cursus-tronc-commun', 'Cursus Tronc Commun'), ('deux-semestres', 'Deux semestres'), ('un-semestre', 'Un semestre')])),
                ('subscription_start', models.DateField(verbose_name='subscription start')),
                ('subscription_end', models.DateField(verbose_name='subscription end')),
                ('payment_method', models.CharField(max_length=255, verbose_name='payment method', choices=[('cheque', 'Chèque'), ('cash', 'Espèce'), ('other', 'Autre')])),
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
            field=models.ForeignKey(to='subscription.Subscriber', related_name='subscriptions'),
        ),
    ]
