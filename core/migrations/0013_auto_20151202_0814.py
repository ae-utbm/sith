# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_auto_20151127_1504'),
    ]

    operations = [
        migrations.CreateModel(
            name='PageRev',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, blank=True, verbose_name='page title')),
                ('content', models.TextField(blank=True, verbose_name='page content')),
                ('date', models.DateTimeField(auto_now=True, verbose_name='date')),
                ('author', models.ForeignKey(to=settings.AUTH_USER_MODEL, related_name='page_rev')),
            ],
            options={
                'ordering': ['date'],
            },
        ),
        migrations.RemoveField(
            model_name='page',
            name='content',
        ),
        migrations.RemoveField(
            model_name='page',
            name='title',
        ),
        migrations.AddField(
            model_name='pagerev',
            name='page',
            field=models.ForeignKey(to='core.Page', related_name='revisions'),
        ),
    ]
