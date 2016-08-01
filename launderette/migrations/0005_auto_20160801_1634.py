# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('counter', '0011_counter_sellers'),
        ('subscription', '0002_auto_20160718_1805'),
        ('launderette', '0004_token_start_date'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='slot',
            options={'verbose_name': 'Slot', 'ordering': ['start_date']},
        ),
        migrations.RemoveField(
            model_name='launderette',
            name='sellers',
        ),
        migrations.AddField(
            model_name='launderette',
            name='counter',
            field=models.OneToOneField(related_name='launderette', default=1, verbose_name='counter', to='counter.Counter'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='token',
            name='borrow_date',
            field=models.DateTimeField(null=True, verbose_name='borrow date'),
        ),
        migrations.AddField(
            model_name='token',
            name='user',
            field=models.ForeignKey(related_name='tokens', default=1, verbose_name='user', to='subscription.Subscriber'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='token',
            name='name',
            field=models.CharField(max_length=5, verbose_name='name'),
        ),
        migrations.AlterUniqueTogether(
            name='token',
            unique_together=set([('name', 'launderette', 'type')]),
        ),
        migrations.RemoveField(
            model_name='token',
            name='start_date',
        ),
    ]
