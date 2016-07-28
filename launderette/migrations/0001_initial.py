# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Launderette',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(max_length=30, verbose_name='name')),
            ],
            options={
                'verbose_name': 'Launderette',
            },
        ),
        migrations.CreateModel(
            name='Machine',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(max_length=30, verbose_name='name')),
                ('is_working', models.BooleanField(default=True, verbose_name='is working')),
                ('launderette', models.ForeignKey(to='launderette.Launderette', related_name='machines', verbose_name='launderette')),
            ],
            options={
                'verbose_name': 'Machine',
            },
        ),
        migrations.CreateModel(
            name='Token',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(max_length=30, verbose_name='name')),
                ('type', models.CharField(choices=[('WASHING', 'Washing'), ('DRYING', 'Drying')], max_length=10, verbose_name='type')),
                ('launderette', models.ForeignKey(to='launderette.Launderette', related_name='tokens', verbose_name='launderette')),
            ],
            options={
                'verbose_name': 'Token',
            },
        ),
    ]
