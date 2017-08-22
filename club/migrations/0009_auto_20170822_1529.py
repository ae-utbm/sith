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
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('email', models.EmailField(verbose_name='Email address', max_length=254, unique=True)),
                ('is_moderated', models.BooleanField(verbose_name='is moderated', default=False)),
                ('club', models.ForeignKey(related_name='mailings', to='club.Club', verbose_name='Club')),
                ('moderator', models.ForeignKey(related_name='moderated_mailings', to=settings.AUTH_USER_MODEL, verbose_name='moderator', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='MailingSubscription',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('email', models.EmailField(verbose_name='Email address', max_length=254)),
                ('mailing', models.ForeignKey(related_name='subscriptions', to='club.Mailing', verbose_name='Mailing')),
                ('user', models.ForeignKey(null=True, related_name='mailing_subscriptions', to=settings.AUTH_USER_MODEL, verbose_name='User', blank=True)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='mailingsubscription',
            unique_together=set([('user', 'email', 'mailing')]),
        ),
    ]
