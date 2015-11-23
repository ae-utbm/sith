# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.contrib.auth.models
import django.db.models.deletion
import django.utils.timezone
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('password', models.CharField(verbose_name='password', max_length=128)),
                ('last_login', models.DateTimeField(blank=True, verbose_name='last login', null=True)),
                ('is_superuser', models.BooleanField(verbose_name='superuser status', help_text='Designates that this user has all permissions without explicitly assigning them.', default=False)),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, max_length=254, verbose_name='username', validators=[django.core.validators.RegexValidator('^[\\w.@+-]+$', 'Enter a valid username. This value may contain only letters, numbers and @/./+/-/_ characters.')], unique=True, help_text='Required. 254 characters or fewer. Letters, digits and @/./+/-/_ only.')),
                ('first_name', models.CharField(verbose_name='first name', max_length=30)),
                ('last_name', models.CharField(verbose_name='last name', max_length=30)),
                ('email', models.EmailField(verbose_name='email address', unique=True, max_length=254)),
                ('date_of_birth', models.DateTimeField(verbose_name='date of birth')),
                ('nick_name', models.CharField(blank=True, max_length=30)),
                ('is_staff', models.BooleanField(verbose_name='staff status', help_text='Designates whether the user can log into this admin site.', default=False)),
                ('is_active', models.BooleanField(verbose_name='active', help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', default=True)),
                ('date_joined', models.DateTimeField(verbose_name='date joined', default=django.utils.timezone.now)),
                ('groups', models.ManyToManyField(related_name='user_set', to='auth.Group', blank=True, verbose_name='groups', related_query_name='user', help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.')),
                ('user_permissions', models.ManyToManyField(related_name='user_set', to='auth.Permission', blank=True, verbose_name='user permissions', related_query_name='user', help_text='Specific permissions for this user.')),
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
                ('full_name', models.CharField(serialize=False, verbose_name='page full name', primary_key=True, max_length=30)),
                ('name', models.CharField(verbose_name='page name', max_length=30)),
                ('title', models.CharField(blank=True, verbose_name='page title', max_length=255)),
                ('content', models.TextField(blank=True, verbose_name='page content')),
                ('revision', models.PositiveIntegerField(verbose_name='current revision', default=1)),
                ('is_locked', models.BooleanField(verbose_name='page mutex', default=False)),
                ('parent', models.ForeignKey(related_name='children', blank=True, null=True, to='core.Page', on_delete=django.db.models.deletion.SET_NULL)),
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
