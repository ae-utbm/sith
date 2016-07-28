# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    replaces = [('launderette', '0001_initial'), ('launderette', '0002_auto_20160728_1858'), ('launderette', '0003_launderette_sellers'), ('launderette', '0004_auto_20160728_1922'), ('launderette', '0005_auto_20160729_0049'), ('launderette', '0006_auto_20160729_0050')]

    dependencies = [
        ('subscription', '0002_auto_20160718_1805'),
    ]

    operations = [
        migrations.CreateModel(
            name='Launderette',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('name', models.CharField(verbose_name='name', max_length=30)),
            ],
            options={
                'verbose_name': 'Launderette',
            },
        ),
        migrations.CreateModel(
            name='Machine',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('name', models.CharField(verbose_name='name', max_length=30)),
                ('is_working', models.BooleanField(verbose_name='is working', default=True)),
                ('launderette', models.ForeignKey(related_name='machines', verbose_name='launderette', to='launderette.Launderette')),
            ],
            options={
                'verbose_name': 'Machine',
            },
        ),
        migrations.CreateModel(
            name='Token',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('name', models.IntegerField(verbose_name='name')),
                ('type', models.CharField(verbose_name='type', choices=[('WASHING', 'Washing'), ('DRYING', 'Drying')], max_length=10)),
                ('launderette', models.ForeignKey(related_name='tokens', verbose_name='launderette', to='launderette.Launderette')),
            ],
            options={
                'verbose_name': 'Token',
            },
        ),
        migrations.CreateModel(
            name='Slot',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('start_date', models.DateTimeField(verbose_name='start date')),
                ('type', models.CharField(verbose_name='type', choices=[('WASHING', 'Washing'), ('DRYING', 'Drying')], max_length=10)),
                ('machine', models.ForeignKey(related_name='slots', verbose_name='machine', to='launderette.Machine')),
                ('token', models.ForeignKey(related_name='slots', null=True, verbose_name='token', blank=True, to='launderette.Token')),
                ('user', models.ForeignKey(related_name='slots', verbose_name='user', to='subscription.Subscriber')),
            ],
        ),
        migrations.AddField(
            model_name='launderette',
            name='sellers',
            field=models.ManyToManyField(verbose_name='sellers', related_name='launderettes', blank=True, to='subscription.Subscriber'),
        ),
    ]
