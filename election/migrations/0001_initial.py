# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscription', '0003_auto_20160902_1914'),
    ]

    operations = [
        migrations.CreateModel(
            name='Candidate',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('votes', models.IntegerField(default=0, verbose_name='votes')),
            ],
        ),
        migrations.CreateModel(
            name='Election',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('title', models.CharField(verbose_name='title', max_length=255)),
                ('description', models.TextField(blank=True, null=True, verbose_name='description')),
                ('start_date', models.DateTimeField(verbose_name='start date')),
                ('end_date', models.DateTimeField(verbose_name='end date')),
            ],
        ),
        migrations.CreateModel(
            name='Responsability',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', auto_created=True, serialize=False)),
                ('title', models.CharField(verbose_name='title', max_length=255)),
                ('description', models.TextField(blank=True, null=True, verbose_name='description')),
                ('blank_votes', models.IntegerField(default=0, verbose_name='blank votes')),
                ('election', models.ForeignKey(to='election.Election', related_name='election', verbose_name='election')),
            ],
        ),
        migrations.AddField(
            model_name='candidate',
            name='responsability',
            field=models.ForeignKey(to='election.Responsability', related_name='responsability', verbose_name='responsability'),
        ),
        migrations.AddField(
            model_name='candidate',
            name='subscriber',
            field=models.ForeignKey(related_name='candidate', to='subscription.Subscriber', blank=True, verbose_name='user'),
        ),
    ]
