# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Club',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('name', models.CharField(max_length=30, verbose_name='name')),
                ('unix_name', models.CharField(validators=[django.core.validators.RegexValidator('^[a-z0-9][a-z0-9._-]*[a-z0-9]$', 'Enter a valid unix name. This value may contain only letters, numbers ./-/_ characters.')], unique=True, max_length=30, verbose_name='unix name', error_messages={'unique': 'A club with that unix name already exists.'})),
                ('address', models.CharField(max_length=254, verbose_name='address')),
                ('edit_groups', models.ManyToManyField(related_name='editable_club', to='core.Group', blank=True)),
                ('owner_group', models.ForeignKey(to='core.Group', related_name='owned_club', default=1)),
                ('parent', models.ForeignKey(to='club.Club', related_name='children', null=True, blank=True)),
                ('view_groups', models.ManyToManyField(related_name='viewable_club', to='core.Group', blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Membership',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('start_date', models.DateField(auto_now=True, verbose_name='start date')),
                ('end_date', models.DateField(blank=True, verbose_name='end date', null=True)),
                ('role', models.IntegerField(choices=[(0, 'Curieux'), (1, 'Membre actif'), (2, 'Membre du bureau'), (3, 'Responsable info'), (4, 'Secrétaire'), (5, 'Responsable com'), (7, 'Trésorier'), (9, 'Vice-Président'), (10, 'Président')], verbose_name='role', default=0)),
                ('description', models.CharField(blank=True, max_length=30, verbose_name='description')),
                ('club', models.ForeignKey(to='club.Club', related_name='members')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='membership')),
            ],
        ),
    ]
