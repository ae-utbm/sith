# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
import django.core.validators
import django.db.models.deletion
from django.conf import settings
import django.contrib.auth.models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('password', models.CharField(verbose_name='password', max_length=128)),
                ('last_login', models.DateTimeField(null=True, blank=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(help_text='Designates that this user has all permissions without explicitly assigning them.', default=False, verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 254 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=254, validators=[django.core.validators.RegexValidator('^[\\w.@+-]+$', 'Enter a valid username. This value may contain only letters, numbers and @/./+/-/_ characters.')], unique=True, verbose_name='username')),
                ('first_name', models.CharField(verbose_name='first name', max_length=30)),
                ('last_name', models.CharField(verbose_name='last name', max_length=30)),
                ('email', models.EmailField(unique=True, verbose_name='email address', max_length=254)),
                ('date_of_birth', models.DateTimeField(verbose_name='date of birth')),
                ('nick_name', models.CharField(blank=True, max_length=30)),
                ('is_staff', models.BooleanField(help_text='Designates whether the user can log into this admin site.', default=False, verbose_name='staff status')),
                ('is_active', models.BooleanField(help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', default=True, verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
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
                ('group_ptr', models.OneToOneField(primary_key=True, to='auth.Group', parent_link=True, serialize=False, auto_created=True)),
            ],
            bases=('auth.group',),
        ),
        migrations.CreateModel(
            name='Page',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('name', models.CharField(verbose_name='page name', max_length=30)),
                ('full_name', models.CharField(blank=True, verbose_name='page name', max_length=255)),
                ('edit_group', models.ManyToManyField(blank=True, to='core.Group', related_name='editable_page')),
                ('owner_group', models.ForeignKey(to='core.Group', default=1, related_name='owned_page')),
                ('parent', models.ForeignKey(null=True, to='core.Page', on_delete=django.db.models.deletion.SET_NULL, blank=True, related_name='children')),
                ('view_group', models.ManyToManyField(blank=True, to='core.Group', related_name='viewable_page')),
            ],
            options={
                'permissions': (('change_prop_page', "Can change the page's properties (groups, ...)"), ('view_page', 'Can view the page')),
            },
        ),
        migrations.CreateModel(
            name='PageRev',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
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
            name='edit_group',
            field=models.ManyToManyField(blank=True, to='core.Group', related_name='editable_user'),
        ),
        migrations.AddField(
            model_name='user',
            name='groups',
            field=models.ManyToManyField(help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', to='auth.Group', blank=True, verbose_name='groups', related_query_name='user', related_name='user_set'),
        ),
        migrations.AddField(
            model_name='user',
            name='owner_group',
            field=models.ForeignKey(to='core.Group', default=1, related_name='owned_user'),
        ),
        migrations.AddField(
            model_name='user',
            name='user_permissions',
            field=models.ManyToManyField(help_text='Specific permissions for this user.', to='auth.Permission', blank=True, verbose_name='user permissions', related_query_name='user', related_name='user_set'),
        ),
        migrations.AddField(
            model_name='user',
            name='view_group',
            field=models.ManyToManyField(blank=True, to='core.Group', related_name='viewable_user'),
        ),
        migrations.AlterUniqueTogether(
            name='page',
            unique_together=set([('name', 'parent')]),
        ),
    ]
