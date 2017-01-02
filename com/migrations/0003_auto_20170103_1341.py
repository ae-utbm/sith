# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('club', '0006_auto_20161229_0040'),
        ('com', '0002_news_newsdate'),
    ]

    operations = [
        migrations.CreateModel(
            name='Weekmail',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('title', models.CharField(verbose_name='title', max_length=64)),
                ('intro', models.TextField(verbose_name='intro', blank=True)),
                ('joke', models.TextField(verbose_name='joke', blank=True)),
                ('protip', models.TextField(verbose_name='protip', blank=True)),
                ('conclusion', models.TextField(verbose_name='conclusion', blank=True)),
                ('sent', models.BooleanField(verbose_name='sent', default=False)),
            ],
            options={
                'ordering': ['-id'],
            },
        ),
        migrations.CreateModel(
            name='WeekmailArticle',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('title', models.CharField(verbose_name='title', max_length=64)),
                ('content', models.TextField(verbose_name='content')),
                ('rank', models.IntegerField(verbose_name='rank', default=-1)),
                ('author', models.ForeignKey(related_name='owned_weekmail_articles', to=settings.AUTH_USER_MODEL, verbose_name='author')),
                ('club', models.ForeignKey(related_name='weekmail_articles', to='club.Club', verbose_name='club')),
                ('weekmail', models.ForeignKey(related_name='articles', to='com.Weekmail', verbose_name='weekmail')),
            ],
        ),
        migrations.AddField(
            model_name='sith',
            name='weekmail_destinations',
            field=models.TextField(verbose_name='weekmail destinations', default=''),
        ),
    ]
