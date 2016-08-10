# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.contrib.auth.models
import core.models
import django.db.models.deletion
import django.core.validators
from django.conf import settings


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
                ('last_login', models.DateTimeField(null=True, verbose_name='last login', blank=True)),
                ('username', models.CharField(verbose_name='username', error_messages={'unique': 'A user with that username already exists.'}, unique=True, max_length=254, help_text='Required. 254 characters or fewer. Letters, digits and @/./+/-/_ only.', validators=[django.core.validators.RegexValidator('^[\\w.@+-]+$', 'Enter a valid username. This value may contain only letters, numbers and @/./+/-/_ characters.')])),
                ('first_name', models.CharField(verbose_name='first name', max_length=30)),
                ('last_name', models.CharField(verbose_name='last name', max_length=30)),
                ('email', models.EmailField(max_length=254, verbose_name='email address', unique=True)),
                ('date_of_birth', models.DateField(null=True, verbose_name='date of birth', blank=True)),
                ('nick_name', models.CharField(max_length=30, blank=True)),
                ('is_staff', models.BooleanField(verbose_name='staff status', default=False, help_text='Designates whether the user can log into this admin site.')),
                ('is_active', models.BooleanField(verbose_name='active', default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.')),
                ('date_joined', models.DateField(verbose_name='date joined', auto_now_add=True)),
                ('is_superuser', models.BooleanField(verbose_name='superuser', default=False, help_text='Designates whether this user is a superuser. ')),
            ],
            options={
                'abstract': False,
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Group',
            fields=[
                ('group_ptr', models.OneToOneField(serialize=False, auto_created=True, to='auth.Group', primary_key=True, parent_link=True)),
                ('is_meta', models.BooleanField(verbose_name='meta group status', default=False, help_text='Whether a group is a meta group or not')),
                ('description', models.CharField(verbose_name='description', max_length=60)),
            ],
            bases=('auth.group',),
        ),
        migrations.CreateModel(
            name='Page',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('name', models.CharField(verbose_name='page name', max_length=30)),
                ('_full_name', models.CharField(verbose_name='page name', max_length=255, blank=True)),
                ('edit_groups', models.ManyToManyField(to='core.Group', verbose_name='edit group', related_name='editable_page', blank=True)),
                ('owner_group', models.ForeignKey(to='core.Group', default=1, related_name='owned_page', verbose_name='owner group')),
                ('parent', models.ForeignKey(to='core.Page', null=True, related_name='children', verbose_name='parent', blank=True, on_delete=django.db.models.deletion.SET_NULL)),
                ('view_groups', models.ManyToManyField(to='core.Group', verbose_name='view group', related_name='viewable_page', blank=True)),
            ],
            options={
                'permissions': (('change_prop_page', "Can change the page's properties (groups, ...)"), ('view_page', 'Can view the page')),
            },
        ),
        migrations.CreateModel(
            name='PageRev',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('revision', models.IntegerField(verbose_name='revision')),
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
        migrations.CreateModel(
            name='Preferences',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('show_my_stats', models.BooleanField(verbose_name='define if we show a users stats', default=False, help_text='Show your account statistics to others')),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL, related_name='preferences')),
            ],
        ),
        migrations.CreateModel(
            name='SithFile',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('name', models.CharField(verbose_name='file name', max_length=30)),
                ('file', models.FileField(null=True, upload_to=core.models.get_directory, verbose_name='file', blank=True)),
                ('is_folder', models.BooleanField(verbose_name='is folder', default=True)),
                ('mime_type', models.CharField(verbose_name='mime type', max_length=30)),
                ('size', models.IntegerField(verbose_name='size', default=0)),
                ('date', models.DateTimeField(verbose_name='date', auto_now=True)),
                ('edit_groups', models.ManyToManyField(to='core.Group', verbose_name='edit group', related_name='editable_files', blank=True)),
                ('owner', models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='owned_files', verbose_name='owner')),
                ('parent', models.ForeignKey(to='core.SithFile', null=True, related_name='children', verbose_name='parent', blank=True)),
                ('view_groups', models.ManyToManyField(to='core.Group', verbose_name='view group', related_name='viewable_files', blank=True)),
            ],
            options={
                'verbose_name': 'file',
            },
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
        migrations.AddField(
            model_name='user',
            name='groups',
            field=models.ManyToManyField(to='core.RealGroup', related_name='users', blank=True),
        ),
    ]
