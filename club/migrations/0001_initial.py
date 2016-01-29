# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.core.validators
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Club',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=30, verbose_name='name')),
                ('unix_name', models.CharField(unique=True, error_messages={'unique': 'A club with that unix name already exists.'}, validators=[django.core.validators.RegexValidator('^[a-z0-9][a-z0-9._-]*[a-z0-9]$', 'Enter a valid unix name. This value may contain only letters, numbers ./-/_ characters.')], verbose_name='unix name', max_length=30)),
                ('address', models.CharField(max_length=254, verbose_name='address')),
                ('parent', models.ForeignKey(related_name='children', blank=True, to='club.Club', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Membership',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('start_date', models.DateField(auto_now=True, verbose_name='start date')),
                ('end_date', models.DateField(null=True, verbose_name='end date', blank=True)),
                ('role', models.IntegerField(verbose_name='role', choices=[(0, 'Membre'), (1, 'Membre actif'), (2, 'Membre du bureau'), (3, 'Responsable info'), (4, 'Secrétaire'), (5, 'Responsable com'), (7, 'Trésorier'), (8, 'Vice-Président'), (9, 'Vice-Président'), (10, 'Président')], default=0)),
                ('description', models.CharField(max_length=30, verbose_name='description', blank=True)),
                ('club', models.ForeignKey(related_name='members', to='club.Club')),
                ('user', models.ForeignKey(related_name='membership', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
