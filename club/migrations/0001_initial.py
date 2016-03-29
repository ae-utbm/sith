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
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('name', models.CharField(max_length=30, verbose_name='name')),
                ('unix_name', models.CharField(unique=True, max_length=30, verbose_name='unix name', error_messages={'unique': 'A club with that unix name already exists.'}, validators=[django.core.validators.RegexValidator('^[a-z0-9][a-z0-9._-]*[a-z0-9]$', 'Enter a valid unix name. This value may contain only letters, numbers ./-/_ characters.')])),
                ('address', models.CharField(max_length=254, verbose_name='address')),
                ('edit_groups', models.ManyToManyField(to='core.Group', blank=True, related_name='editable_club')),
                ('owner_group', models.ForeignKey(default=1, related_name='owned_club', to='core.Group')),
                ('parent', models.ForeignKey(blank=True, related_name='children', to='club.Club', null=True)),
                ('view_groups', models.ManyToManyField(to='core.Group', blank=True, related_name='viewable_club')),
            ],
        ),
        migrations.CreateModel(
            name='Membership',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('start_date', models.DateField(auto_now=True, verbose_name='start date')),
                ('end_date', models.DateField(blank=True, null=True, verbose_name='end date')),
                ('role', models.IntegerField(choices=[(0, 'Curieux'), (1, 'Membre actif'), (2, 'Membre du bureau'), (3, 'Responsable info'), (4, 'Secrétaire'), (5, 'Responsable com'), (7, 'Trésorier'), (9, 'Vice-Président'), (10, 'Président')], verbose_name='role', default=0)),
                ('description', models.CharField(max_length=30, blank=True, verbose_name='description')),
                ('club', models.ForeignKey(to='club.Club', related_name='members')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='membership')),
            ],
        ),
    ]
