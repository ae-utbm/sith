# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.core.validators
import django.db.models.deletion
import core.models
import django.contrib.auth.models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(verbose_name='last login', null=True, blank=True)),
                ('is_superuser', models.BooleanField(verbose_name='superuser status', default=False, help_text='Designates that this user has all permissions without explicitly assigning them.')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, verbose_name='username', help_text='Required. 254 characters or fewer. Letters, digits and @/./+/-/_ only.', unique=True, validators=[django.core.validators.RegexValidator('^[\\w.@+-]+$', 'Enter a valid username. This value may contain only letters, numbers and @/./+/-/_ characters.')], max_length=254)),
                ('first_name', models.CharField(max_length=30, verbose_name='first name')),
                ('last_name', models.CharField(max_length=30, verbose_name='last name')),
                ('email', models.EmailField(max_length=254, verbose_name='email address', unique=True)),
                ('date_of_birth', models.DateField(verbose_name='date of birth')),
                ('nick_name', models.CharField(max_length=30, blank=True)),
                ('is_staff', models.BooleanField(verbose_name='staff status', default=False, help_text='Designates whether the user can log into this admin site.')),
                ('is_active', models.BooleanField(verbose_name='active', default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.')),
                ('date_joined', models.DateField(verbose_name='date joined', auto_now_add=True)),
            ],
            options={
                'verbose_name_plural': 'users',
                'verbose_name': 'user',
                'permissions': (('change_prop_user', "Can change the user's properties (groups, ...)"), ('view_user', "Can view user's profile")),
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Group',
            fields=[
                ('group_ptr', models.OneToOneField(to='auth.Group', auto_created=True, parent_link=True, primary_key=True, serialize=False)),
                ('is_meta', models.BooleanField(verbose_name='meta group status', default=False, help_text='Whether a group is a meta group or not')),
            ],
            bases=('auth.group',),
        ),
        migrations.CreateModel(
            name='Page',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('name', models.CharField(max_length=30, verbose_name='page name')),
                ('_full_name', models.CharField(verbose_name='page name', max_length=255, blank=True)),
                ('edit_groups', models.ManyToManyField(to='core.Group', blank=True, related_name='editable_page')),
                ('owner_group', models.ForeignKey(to='core.Group', default=1, related_name='owned_page')),
                ('parent', models.ForeignKey(to='core.Page', on_delete=django.db.models.deletion.SET_NULL, related_name='children', null=True, blank=True)),
                ('view_groups', models.ManyToManyField(to='core.Group', blank=True, related_name='viewable_page')),
            ],
            options={
                'permissions': (('change_prop_page', "Can change the page's properties (groups, ...)"), ('view_page', 'Can view the page')),
            },
        ),
        migrations.CreateModel(
            name='PageRev',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('title', models.CharField(verbose_name='page title', max_length=255, blank=True)),
                ('content', models.TextField(verbose_name='page content', blank=True)),
                ('date', models.DateTimeField(verbose_name='date', auto_now=True)),
                ('author', models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='page_rev')),
                ('page', models.ForeignKey(to='core.Page', related_name='revisions')),
            ],
            options={
                'ordering': ['date'],
            },
        ),
        migrations.AddField(
            model_name='user',
            name='edit_groups',
            field=models.ManyToManyField(to='core.Group', blank=True, related_name='editable_user'),
        ),
        migrations.AddField(
            model_name='user',
            name='groups',
            field=models.ManyToManyField(to='auth.Group', verbose_name='groups', help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_query_name='user', blank=True, related_name='user_set'),
        ),
        migrations.AddField(
            model_name='user',
            name='owner_group',
            field=models.ForeignKey(to='core.Group', default=1, related_name='owned_user'),
        ),
        migrations.AddField(
            model_name='user',
            name='user_permissions',
            field=models.ManyToManyField(to='auth.Permission', verbose_name='user permissions', help_text='Specific permissions for this user.', related_query_name='user', blank=True, related_name='user_set'),
        ),
        migrations.AddField(
            model_name='user',
            name='view_groups',
            field=models.ManyToManyField(to='core.Group', blank=True, related_name='viewable_user'),
        ),
        migrations.CreateModel(
            name='MetaGroup',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('core.group',),
            managers=[
                ('objects', core.models.MetaGroupManager()),
            ],
        ),
        migrations.CreateModel(
            name='RealGroup',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('core.group',),
            managers=[
                ('objects', core.models.RealGroupManager()),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='page',
            unique_together=set([('name', 'parent')]),
        ),
    ]
