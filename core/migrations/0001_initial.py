# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.core.validators
from django.conf import settings
import django.db.models.deletion
import django.contrib.auth.models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, verbose_name='last login', null=True)),
                ('is_superuser', models.BooleanField(help_text='Designates that this user has all permissions without explicitly assigning them.', default=False, verbose_name='superuser status')),
                ('username', models.CharField(max_length=254, verbose_name='username', unique=True, help_text='Required. 254 characters or fewer. Letters, digits and @/./+/-/_ only.', validators=[django.core.validators.RegexValidator('^[\\w.@+-]+$', 'Enter a valid username. This value may contain only letters, numbers and @/./+/-/_ characters.')], error_messages={'unique': 'A user with that username already exists.'})),
                ('first_name', models.CharField(max_length=30, verbose_name='first name')),
                ('last_name', models.CharField(max_length=30, verbose_name='last name')),
                ('email', models.EmailField(max_length=254, verbose_name='email address', unique=True)),
                ('date_of_birth', models.DateField(verbose_name='date of birth')),
                ('nick_name', models.CharField(max_length=30, blank=True)),
                ('is_staff', models.BooleanField(help_text='Designates whether the user can log into this admin site.', default=False, verbose_name='staff status')),
                ('is_active', models.BooleanField(help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', default=True, verbose_name='active')),
                ('date_joined', models.DateField(auto_now_add=True, verbose_name='date joined')),
            ],
            options={
                'verbose_name_plural': 'users',
                'permissions': (('change_prop_user', "Can change the user's properties (groups, ...)"), ('view_user', "Can view user's profile")),
                'verbose_name': 'user',
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Group',
            fields=[
                ('group_ptr', models.OneToOneField(serialize=False, primary_key=True, parent_link=True, to='auth.Group', auto_created=True)),
            ],
            bases=('auth.group',),
        ),
        migrations.CreateModel(
            name='Page',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('name', models.CharField(max_length=30, verbose_name='page name')),
                ('_full_name', models.CharField(max_length=255, verbose_name='page name', blank=True)),
                ('edit_groups', models.ManyToManyField(to='core.Group', related_name='editable_page', blank=True)),
                ('owner_group', models.ForeignKey(to='core.Group', related_name='owned_page', default=1)),
                ('parent', models.ForeignKey(to='core.Page', on_delete=django.db.models.deletion.SET_NULL, null=True, related_name='children', blank=True)),
                ('view_groups', models.ManyToManyField(to='core.Group', related_name='viewable_page', blank=True)),
            ],
            options={
                'permissions': (('change_prop_page', "Can change the page's properties (groups, ...)"), ('view_page', 'Can view the page')),
            },
        ),
        migrations.CreateModel(
            name='PageRev',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='page title', blank=True)),
                ('content', models.TextField(verbose_name='page content', blank=True)),
                ('date', models.DateTimeField(auto_now=True, verbose_name='date')),
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
            field=models.ManyToManyField(to='core.Group', related_name='editable_user', blank=True),
        ),
        migrations.AddField(
            model_name='user',
            name='groups',
            field=models.ManyToManyField(to='auth.Group', related_query_name='user', verbose_name='groups', related_name='user_set', help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', blank=True),
        ),
        migrations.AddField(
            model_name='user',
            name='owner_group',
            field=models.ForeignKey(to='core.Group', related_name='owned_user', default=1),
        ),
        migrations.AddField(
            model_name='user',
            name='user_permissions',
            field=models.ManyToManyField(to='auth.Permission', related_query_name='user', verbose_name='user permissions', related_name='user_set', help_text='Specific permissions for this user.', blank=True),
        ),
        migrations.AddField(
            model_name='user',
            name='view_groups',
            field=models.ManyToManyField(to='core.Group', related_name='viewable_user', blank=True),
        ),
        migrations.AlterUniqueTogether(
            name='page',
            unique_together=set([('name', 'parent')]),
        ),
    ]
