# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import core.models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_pagerev_revision'),
    ]

    operations = [
        migrations.CreateModel(
            name='SithFile',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=30, verbose_name='file name')),
                ('file', models.FileField(upload_to=core.models.get_directory, blank=True, null=True, verbose_name='file')),
                ('is_folder', models.BooleanField(default=True, verbose_name='is folder')),
                ('mime_type', models.CharField(max_length=30, verbose_name='mime type')),
                ('size', models.IntegerField(default=0, verbose_name='size')),
                ('date', models.DateTimeField(auto_now=True, verbose_name='date')),
                ('edit_groups', models.ManyToManyField(to='core.Group', blank=True, verbose_name='edit group', related_name='editable_files')),
                ('owner', models.ForeignKey(related_name='owned_files', to=settings.AUTH_USER_MODEL, verbose_name='owner')),
                ('parent', models.ForeignKey(blank=True, related_name='children', to='core.SithFile', null=True, verbose_name='parent')),
                ('view_groups', models.ManyToManyField(to='core.Group', blank=True, verbose_name='view group', related_name='viewable_files')),
            ],
            options={
                'verbose_name': 'file',
            },
        ),
        migrations.AlterField(
            model_name='page',
            name='edit_groups',
            field=models.ManyToManyField(to='core.Group', blank=True, verbose_name='edit group', related_name='editable_page'),
        ),
        migrations.AlterField(
            model_name='page',
            name='owner_group',
            field=models.ForeignKey(default=1, related_name='owned_page', to='core.Group', verbose_name='owner group'),
        ),
        migrations.AlterField(
            model_name='page',
            name='parent',
            field=models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, blank=True, related_name='children', to='core.Page', null=True, verbose_name='parent'),
        ),
        migrations.AlterField(
            model_name='page',
            name='view_groups',
            field=models.ManyToManyField(to='core.Group', blank=True, verbose_name='view group', related_name='viewable_page'),
        ),
    ]
