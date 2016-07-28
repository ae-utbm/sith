# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscription', '0002_auto_20160718_1805'),
        ('launderette', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Slot',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('start_date', models.DateTimeField(verbose_name='start date')),
                ('type', models.CharField(max_length=10, verbose_name='type', choices=[('WASHING', 'Washing'), ('DRYING', 'Drying')])),
                ('machine', models.ForeignKey(verbose_name='machine', related_name='slots', to='launderette.Machine')),
            ],
        ),
        migrations.AlterField(
            model_name='token',
            name='name',
            field=models.IntegerField(verbose_name='name'),
        ),
        migrations.AddField(
            model_name='slot',
            name='token',
            field=models.ForeignKey(verbose_name='token', related_name='slots', to='launderette.Token'),
        ),
        migrations.AddField(
            model_name='slot',
            name='user',
            field=models.ForeignKey(verbose_name='user', related_name='slots', to='subscription.Subscriber'),
        ),
    ]
