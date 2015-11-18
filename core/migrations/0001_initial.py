# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
import django.core.validators
import django.contrib.auth.models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('password', models.CharField(verbose_name='password', max_length=128)),
                ('last_login', models.DateTimeField(null=True, blank=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(validators=[django.core.validators.RegexValidator('^[\\w.@+-]+$', 'Enter a valid username. This value may contain only letters, numbers and @/./+/-/_ characters.')], help_text='Required. 254 characters or fewer. Letters, digits and @/./+/-/_ only.', error_messages={'unique': 'A user with that username already exists.'}, verbose_name='username', unique=True, max_length=254)),
                ('first_name', models.CharField(verbose_name='first name', max_length=30)),
                ('last_name', models.CharField(verbose_name='last name', max_length=30)),
                ('email', models.EmailField(verbose_name='email address', unique=True, max_length=254)),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('date_of_birth', models.DateTimeField(verbose_name='date of birth')),
                ('nick_name', models.CharField(blank=True, max_length=30)),
                ('groups', models.ManyToManyField(related_query_name='user', help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', blank=True, to='auth.Group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(related_query_name='user', help_text='Specific permissions for this user.', related_name='user_set', blank=True, to='auth.Permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name_plural': 'users',
                'verbose_name': 'user',
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
    ]
