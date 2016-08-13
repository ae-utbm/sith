# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import phonenumber_field.modelfields
from django.utils.timezone import utc
import datetime
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_auto_20160811_0450'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='address',
            field=models.CharField(default='', verbose_name='address', max_length=128, blank=True),
        ),
        migrations.AddField(
            model_name='user',
            name='last_update',
            field=models.DateField(default=datetime.datetime(2016, 8, 13, 3, 22, 21, 699918, tzinfo=utc), verbose_name='last update', auto_now=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='user',
            name='parent_address',
            field=models.CharField(default='', verbose_name='parent address', max_length=128, blank=True),
        ),
        migrations.AddField(
            model_name='user',
            name='parent_phone',
            field=phonenumber_field.modelfields.PhoneNumberField(blank=True, verbose_name='parent phone', max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='phone',
            field=phonenumber_field.modelfields.PhoneNumberField(blank=True, verbose_name='phone', max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='second_email',
            field=models.EmailField(blank=True, verbose_name='second email address', max_length=254, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='avatar_pict',
            field=models.OneToOneField(verbose_name='avatar', on_delete=django.db.models.deletion.SET_NULL, related_name='avatar_of', blank=True, to='core.SithFile', null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='department',
            field=models.CharField(default='NA', verbose_name='department', max_length=15, choices=[('TC', 'TC'), ('IMSI', 'IMSI'), ('IMAP', 'IMAP'), ('INFO', 'INFO'), ('GI', 'GI'), ('E', 'E'), ('EE', 'EE'), ('GESC', 'GESC'), ('GMC', 'GMC'), ('MC', 'MC'), ('EDIM', 'EDIM'), ('HUMA', 'Humanities'), ('NA', 'N/A')], blank=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='dpt_option',
            field=models.CharField(default='', verbose_name='dpt option', max_length=32, blank=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='first_name',
            field=models.CharField(verbose_name='first name', max_length=64),
        ),
        migrations.AlterField(
            model_name='user',
            name='forum_signature',
            field=models.TextField(default='', verbose_name='forum signature', max_length=256, blank=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='last_name',
            field=models.CharField(verbose_name='last name', max_length=64),
        ),
        migrations.AlterField(
            model_name='user',
            name='nick_name',
            field=models.CharField(blank=True, verbose_name='nick name', max_length=64, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='profile_pict',
            field=models.OneToOneField(verbose_name='profile', on_delete=django.db.models.deletion.SET_NULL, related_name='profile_of', blank=True, to='core.SithFile', null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='quote',
            field=models.CharField(default='', verbose_name='quote', max_length=256, blank=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(default='', verbose_name='role', max_length=15, choices=[('STUDENT', 'Student'), ('ADMINISTRATIVE', 'Administrative agent'), ('TEACHER', 'Teacher'), ('AGENT', 'Agent'), ('DOCTOR', 'Doctor'), ('FORMER STUDENT', 'Former student'), ('SERVICE', 'Service')], blank=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='school',
            field=models.CharField(default='', verbose_name='school', max_length=80, blank=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='scrub_pict',
            field=models.OneToOneField(verbose_name='scrub', on_delete=django.db.models.deletion.SET_NULL, related_name='scrub_of', blank=True, to='core.SithFile', null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='semester',
            field=models.CharField(default='', verbose_name='semester', max_length=5, blank=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='tshirt_size',
            field=models.CharField(default='-', verbose_name='tshirt size', max_length=5, choices=[('-', '-'), ('XS', 'XS'), ('S', 'S'), ('M', 'M'), ('L', 'L'), ('XL', 'XL'), ('XXL', 'XXL'), ('XXXL', 'XXXL')]),
        ),
    ]
