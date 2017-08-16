# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('club', '0008_auto_20170515_2214'),
    ]

    operations = [
        migrations.CreateModel(
            name='Mailing',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('email', models.EmailField(verbose_name='Email address', unique=True, max_length=254)),
                ('club', models.ForeignKey(verbose_name='Club', related_name='mailings', to='club.Club')),
            ],
        ),
        migrations.CreateModel(
            name='MailingSubscription',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('email', models.EmailField(verbose_name='Email address', max_length=254, unique=True)),
                ('mailing', models.ForeignKey(verbose_name='Mailing', related_name='subscriptions', to='club.Mailing')),
                ('user', models.ForeignKey(null=True, verbose_name='User', related_name='mailing_subscriptions', to=settings.AUTH_USER_MODEL, blank=True)),
            ],
        ),
    ]
