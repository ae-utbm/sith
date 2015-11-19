# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Page',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('name', models.CharField(max_length=30, verbose_name='page name')),
                ('full_name', models.CharField(max_length=255, verbose_name='full name')),
                ('content', models.TextField(blank=True, verbose_name='page content')),
                ('revision', models.PositiveIntegerField(default=1, verbose_name='current revision')),
                ('is_locked', models.BooleanField(default=False, verbose_name='page mutex')),
            ],
            options={
                'permissions': (('can_edit', 'Can edit the page'), ('can_view', 'Can view the page')),
            },
        ),
        migrations.AlterField(
            model_name='user',
            name='date_of_birth',
            field=models.DateTimeField(default='1970-01-01T00:00:00+01:00', verbose_name='date of birth'),
        ),
    ]
