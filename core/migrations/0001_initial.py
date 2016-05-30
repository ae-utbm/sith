# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import django.core.validators
import django.db.models.deletion
import core.models
import django.contrib.auth.models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('password', models.CharField(verbose_name='password', max_length=128)),
                ('last_login', models.DateTimeField(blank=True, verbose_name='last login', null=True)),
                ('is_superuser', models.BooleanField(verbose_name='superuser status', default=False, help_text='Designates that this user has all permissions without explicitly assigning them.')),
                ('username', models.CharField(verbose_name='username', max_length=254, error_messages={'unique': 'A user with that username already exists.'}, validators=[django.core.validators.RegexValidator('^[\\w.@+-]+$', 'Enter a valid username. This value may contain only letters, numbers and @/./+/-/_ characters.')], help_text='Required. 254 characters or fewer. Letters, digits and @/./+/-/_ only.', unique=True)),
                ('first_name', models.CharField(verbose_name='first name', max_length=30)),
                ('last_name', models.CharField(verbose_name='last name', max_length=30)),
                ('email', models.EmailField(verbose_name='email address', max_length=254, unique=True)),
                ('date_of_birth', models.DateField(verbose_name='date of birth')),
                ('nick_name', models.CharField(blank=True, max_length=30)),
                ('is_staff', models.BooleanField(verbose_name='staff status', default=False, help_text='Designates whether the user can log into this admin site.')),
                ('is_active', models.BooleanField(verbose_name='active', default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.')),
                ('date_joined', models.DateField(verbose_name='date joined', auto_now_add=True)),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'permissions': (('change_prop_user', "Can change the user's properties (groups, ...)"), ('view_user', "Can view user's profile")),
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Group',
            fields=[
                ('group_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, to='auth.Group', serialize=False)),
                ('is_meta', models.BooleanField(verbose_name='meta group status', default=False, help_text='Whether a group is a meta group or not')),
                ('description', models.CharField(verbose_name='description', max_length=60)),
            ],
            bases=('auth.group',),
        ),
        migrations.CreateModel(
            name='Page',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('name', models.CharField(verbose_name='page name', max_length=30)),
                ('_full_name', models.CharField(blank=True, verbose_name='page name', max_length=255)),
                ('edit_groups', models.ManyToManyField(blank=True, to='core.Group', related_name='editable_page')),
                ('owner_group', models.ForeignKey(default=1, related_name='owned_page', to='core.Group')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.Page', related_name='children')),
                ('view_groups', models.ManyToManyField(blank=True, to='core.Group', related_name='viewable_page')),
            ],
            options={
                'permissions': (('change_prop_page', "Can change the page's properties (groups, ...)"), ('view_page', 'Can view the page')),
            },
        ),
        migrations.CreateModel(
            name='PageRev',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('title', models.CharField(blank=True, verbose_name='page title', max_length=255)),
                ('content', models.TextField(blank=True, verbose_name='page content')),
                ('date', models.DateTimeField(verbose_name='date', auto_now=True)),
                ('author', models.ForeignKey(related_name='page_rev', to=settings.AUTH_USER_MODEL)),
                ('page', models.ForeignKey(related_name='revisions', to='core.Page')),
            ],
            options={
                'ordering': ['date'],
            },
        ),
        migrations.AddField(
            model_name='user',
            name='edit_groups',
            field=models.ManyToManyField(blank=True, to='core.Group', related_name='editable_user'),
        ),
        migrations.AddField(
            model_name='user',
            name='groups',
            field=models.ManyToManyField(blank=True, verbose_name='groups', related_name='user_set', related_query_name='user', to='auth.Group', help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.'),
        ),
        migrations.AddField(
            model_name='user',
            name='owner_group',
            field=models.ForeignKey(default=1, related_name='owned_user', to='core.Group'),
        ),
        migrations.AddField(
            model_name='user',
            name='user_permissions',
            field=models.ManyToManyField(blank=True, verbose_name='user permissions', related_name='user_set', related_query_name='user', to='auth.Permission', help_text='Specific permissions for this user.'),
        ),
        migrations.AddField(
            model_name='user',
            name='view_groups',
            field=models.ManyToManyField(blank=True, to='core.Group', related_name='viewable_user'),
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
