# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('launderette', '0001_initial'),
        ('counter', '0001_initial'),
        ('subscription', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='token',
            name='user',
            field=models.ForeignKey(verbose_name='user', null=True, to='subscription.Subscriber', related_name='tokens', blank=True),
        ),
        migrations.AddField(
            model_name='slot',
            name='machine',
            field=models.ForeignKey(verbose_name='machine', related_name='slots', to='launderette.Machine'),
        ),
        migrations.AddField(
            model_name='slot',
            name='token',
            field=models.ForeignKey(verbose_name='token', null=True, to='launderette.Token', related_name='slots', blank=True),
        ),
        migrations.AddField(
            model_name='slot',
            name='user',
            field=models.ForeignKey(verbose_name='user', related_name='slots', to='subscription.Subscriber'),
        ),
        migrations.AddField(
            model_name='machine',
            name='launderette',
            field=models.ForeignKey(verbose_name='launderette', related_name='machines', to='launderette.Launderette'),
        ),
        migrations.AddField(
            model_name='launderette',
            name='counter',
            field=models.OneToOneField(verbose_name='counter', related_name='launderette', to='counter.Counter'),
        ),
        migrations.AlterUniqueTogether(
            name='token',
            unique_together=set([('name', 'launderette', 'type')]),
        ),
    ]
