# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import core.models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_auto_20160811_0206'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='department',
            field=models.CharField(max_length=15, choices=[('TC', 'TC'), ('IMSI', 'IMSI'), ('IMAP', 'IMAP'), ('INFO', 'INFO'), ('GI', 'GI'), ('E', 'E'), ('EE', 'EE'), ('GESC', 'GESC'), ('GMC', 'GMC'), ('MC', 'MC'), ('EDIM', 'EDIM'), ('HUMAN', 'Humanities'), ('NA', 'N/A')], default='NA', verbose_name='department'),
        ),
        migrations.AddField(
            model_name='user',
            name='dpt_option',
            field=models.CharField(max_length=32, default='', verbose_name='dpt option'),
        ),
        migrations.AddField(
            model_name='user',
            name='forum_signature',
            field=models.TextField(max_length=256, default='', verbose_name='forum signature'),
        ),
        migrations.AddField(
            model_name='user',
            name='promo',
            field=models.IntegerField(blank=True, null=True, validators=[core.models.validate_promo], verbose_name='promo'),
        ),
        migrations.AddField(
            model_name='user',
            name='quote',
            field=models.CharField(max_length=64, default='', verbose_name='quote'),
        ),
        migrations.AddField(
            model_name='user',
            name='role',
            field=models.CharField(max_length=15, choices=[('STUDENT', 'Student'), ('ADMINISTRATIVE', 'Administrative agent'), ('TEACHER', 'Teacher'), ('AGENT', 'Agent'), ('DOCTOR', 'Doctor'), ('FORMER STUDENT', 'Former student'), ('SERVICE', 'Service')], default='STUDENT', verbose_name='role'),
        ),
        migrations.AddField(
            model_name='user',
            name='school',
            field=models.CharField(max_length=32, default='', verbose_name='school'),
        ),
        migrations.AddField(
            model_name='user',
            name='semester',
            field=models.CharField(max_length=5, default='', verbose_name='semester'),
        ),
        migrations.AddField(
            model_name='user',
            name='sex',
            field=models.CharField(max_length=10, choices=[('MAN', 'Man'), ('WOMAN', 'Woman')], default='MAN', verbose_name='sex'),
        ),
        migrations.AddField(
            model_name='user',
            name='tshirt_size',
            field=models.CharField(max_length=5, choices=[('-', '-'), ('XS', 'XS'), ('S', 'S'), ('M', 'M'), ('L', 'L'), ('XL', 'XL'), ('XXL', 'XXL'), ('XXXL', 'XXXL')], default='M', verbose_name='tshirt size'),
        ),
    ]
