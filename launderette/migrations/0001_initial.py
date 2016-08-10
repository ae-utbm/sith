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
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('name', models.CharField(verbose_name='name', max_length=30)),
            ],
            options={
                'verbose_name': 'Launderette',
            },
        ),
        migrations.CreateModel(
            name='Machine',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('name', models.CharField(verbose_name='name', max_length=30)),
                ('type', models.CharField(verbose_name='type', max_length=10, choices=[('WASHING', 'Washing'), ('DRYING', 'Drying')])),
                ('is_working', models.BooleanField(default=True, verbose_name='is working')),
            ],
            options={
                'verbose_name': 'Machine',
            },
        ),
        migrations.CreateModel(
            name='Slot',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('start_date', models.DateTimeField(verbose_name='start date')),
                ('type', models.CharField(verbose_name='type', max_length=10, choices=[('WASHING', 'Washing'), ('DRYING', 'Drying')])),
            ],
            options={
                'verbose_name': 'Slot',
                'ordering': ['start_date'],
            },
        ),
        migrations.CreateModel(
            name='Token',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('name', models.CharField(verbose_name='name', max_length=5)),
                ('type', models.CharField(verbose_name='type', max_length=10, choices=[('WASHING', 'Washing'), ('DRYING', 'Drying')])),
                ('borrow_date', models.DateTimeField(verbose_name='borrow date', null=True, blank=True)),
                ('launderette', models.ForeignKey(verbose_name='launderette', related_name='tokens', to='launderette.Launderette')),
            ],
            options={
                'verbose_name': 'Token',
                'ordering': ['type', 'name'],
            },
        ),
    ]
