# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_auto_20151215_0827'),
    ]

    operations = [
        migrations.CreateModel(
            name='Member',
            fields=[
                ('user', models.OneToOneField(primary_key=True, to=settings.AUTH_USER_MODEL, serialize=False)),
            ],
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('subscription_type', models.CharField(choices=[('cursus branche', 'Cursus Branche'), ('cursus tronc commun', 'Cursus Tronc Commun'), ('deux semestres', 'Deux semestres'), ('un semestre', 'Un semestre')], verbose_name='subscription type', max_length=255)),
                ('subscription_start', models.DateField(verbose_name='subscription start')),
                ('subscription_end', models.DateField(verbose_name='subscription end')),
                ('payment_method', models.CharField(choices=[('cheque', 'Chèque'), ('cash', 'Espèce'), ('other', 'Autre')], verbose_name='payment method', max_length=255)),
                ('member', models.ForeignKey(related_name='subscriptions', to='ae.Member')),
            ],
            options={
                'ordering': ['subscription_start'],
            },
        ),
    ]
