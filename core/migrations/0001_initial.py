# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django.contrib.auth.models
import django.core.validators
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('password', models.CharField(verbose_name='password', max_length=128)),
                ('last_login', models.DateTimeField(verbose_name='last login', blank=True, null=True)),
                ('is_superuser', models.BooleanField(verbose_name='superuser status', help_text='Designates that this user has all permissions without explicitly assigning them.', default=False)),
                ('username', models.CharField(help_text='Required. 254 characters or fewer. Letters, digits and @/./+/-/_ only.', unique=True, verbose_name='username', error_messages={'unique': 'A user with that username already exists.'}, validators=[django.core.validators.RegexValidator('^[\\w.@+-]+$', 'Enter a valid username. This value may contain only letters, numbers and @/./+/-/_ characters.')], max_length=254)),
                ('first_name', models.CharField(verbose_name='first name', max_length=30)),
                ('last_name', models.CharField(verbose_name='last name', max_length=30)),
                ('email', models.EmailField(verbose_name='email address', max_length=254, unique=True)),
                ('date_of_birth', models.DateTimeField(verbose_name='date of birth')),
                ('nick_name', models.CharField(blank=True, max_length=30)),
                ('is_staff', models.BooleanField(verbose_name='staff status', help_text='Designates whether the user can log into this admin site.', default=False)),
                ('is_active', models.BooleanField(verbose_name='active', help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', default=True)),
                ('date_joined', models.DateTimeField(verbose_name='date joined', default=django.utils.timezone.now)),
                ('groups', models.ManyToManyField(related_name='user_set', related_query_name='user', help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', verbose_name='groups', blank=True, to='auth.Group')),
                ('user_permissions', models.ManyToManyField(related_name='user_set', related_query_name='user', help_text='Specific permissions for this user.', verbose_name='user permissions', blank=True, to='auth.Permission')),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Page',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('name', models.CharField(verbose_name='page name', max_length=30)),
                ('title', models.CharField(verbose_name='page title', blank=True, max_length=255)),
                ('content', models.TextField(verbose_name='page content', blank=True)),
                ('revision', models.PositiveIntegerField(verbose_name='current revision', default=1)),
                ('is_locked', models.BooleanField(verbose_name='page mutex', default=False)),
                ('parent', models.ForeignKey(related_name='children', to='core.Page', blank=True, on_delete=django.db.models.deletion.SET_NULL, null=True)),
            ],
            options={
                'permissions': (('can_edit', 'Can edit the page'), ('can_view', 'Can view the page')),
            },
        ),
        migrations.AlterUniqueTogether(
            name='page',
            unique_together=set([('name', 'parent')]),
        ),
    ]
