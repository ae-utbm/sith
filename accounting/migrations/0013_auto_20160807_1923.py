# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0012_auto_20160720_1847'),
    ]

    operations = [
        migrations.CreateModel(
            name='Company',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('name', models.CharField(max_length=60, verbose_name='name')),
            ],
            options={
                'verbose_name': 'company',
            },
        ),
        migrations.AddField(
            model_name='operation',
            name='target_id',
            field=models.IntegerField(blank=True, null=True, verbose_name='target id'),
        ),
        migrations.AddField(
            model_name='operation',
            name='target_label',
            field=models.CharField(max_length=32, blank=True, default='', verbose_name='target label'),
        ),
        migrations.AddField(
            model_name='operation',
            name='target_type',
            field=models.CharField(max_length=10, default='OTHER', choices=[('USER', 'User'), ('CLUB', 'Club'), ('ACCOUNT', 'Account'), ('COMPANY', 'Company'), ('OTHER', 'Other')], verbose_name='target type'),
            preserve_default=False,
        ),
    ]
