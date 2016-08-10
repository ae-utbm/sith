# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.core.validators
from django.conf import settings


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
                ('name', models.CharField(verbose_name='name', max_length=30)),
                ('unix_name', models.CharField(verbose_name='unix name', unique=True, error_messages={'unique': 'A club with that unix name already exists.'}, max_length=30, validators=[django.core.validators.RegexValidator('^[a-z0-9][a-z0-9._-]*[a-z0-9]$', 'Enter a valid unix name. This value may contain only letters, numbers ./-/_ characters.')])),
                ('address', models.CharField(verbose_name='address', max_length=254)),
                ('edit_groups', models.ManyToManyField(to='core.Group', related_name='editable_club', blank=True)),
                ('owner_group', models.ForeignKey(related_name='owned_club', default=1, to='core.Group')),
                ('parent', models.ForeignKey(blank=True, null=True, to='club.Club', related_name='children')),
                ('view_groups', models.ManyToManyField(to='core.Group', related_name='viewable_club', blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='Membership',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('start_date', models.DateField(verbose_name='start date', auto_now=True)),
                ('end_date', models.DateField(verbose_name='end date', null=True, blank=True)),
                ('role', models.IntegerField(default=0, verbose_name='role', choices=[(0, 'Curious'), (1, 'Active member'), (2, 'Board member'), (3, 'IT supervisor'), (4, 'Secretary'), (5, 'Communication supervisor'), (7, 'Treasurer'), (9, 'Vice-President'), (10, 'President')])),
                ('description', models.CharField(verbose_name='description', max_length=30, blank=True)),
                ('club', models.ForeignKey(verbose_name='club', related_name='members', to='club.Club')),
                ('user', models.ForeignKey(verbose_name='user', related_name='membership', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
