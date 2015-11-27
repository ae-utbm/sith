# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_auto_20151127_1504'),
    ]

    operations = [
        migrations.CreateModel(
            name='PageRevision',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('title', models.CharField(blank=True, verbose_name='page title', max_length=255)),
                ('content', models.TextField(blank=True, verbose_name='page content')),
            ],
        ),
        migrations.RemoveField(
            model_name='page',
            name='content',
        ),
        migrations.RemoveField(
            model_name='page',
            name='revision',
        ),
        migrations.RemoveField(
            model_name='page',
            name='title',
        ),
        migrations.AddField(
            model_name='pagerevision',
            name='parent_page',
            field=models.ForeignKey(related_name='revisions', to='core.Page'),
        ),
        migrations.AddField(
            model_name='page',
            name='last_revision',
            field=models.OneToOneField(to='core.PageRevision', default=1),
            preserve_default=False,
        ),
    ]
