# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_auto_20160128_0842'),
    ]

    operations = [
        migrations.CreateModel(
            name='Member',
            fields=[
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL, primary_key=True, serialize=False)),
            ],
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('subscription_type', models.CharField(choices=[('cursus-branche', 'Cursus Branche'), ('cursus-tronc-commun', 'Cursus Tronc Commun'), ('deux-semestres', 'Deux semestres'), ('un-semestre', 'Un semestre')], verbose_name='subscription type', max_length=255)),
                ('subscription_start', models.DateField(verbose_name='subscription start')),
                ('subscription_end', models.DateField(verbose_name='subscription end')),
                ('payment_method', models.CharField(choices=[('cheque', 'Chèque'), ('cash', 'Espèce'), ('other', 'Autre')], verbose_name='payment method', max_length=255)),
                ('member', models.ForeignKey(to='subscription.Member', related_name='subscriptions')),
            ],
            options={
                'ordering': ['subscription_start'],
            },
        ),
    ]
