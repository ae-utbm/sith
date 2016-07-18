# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('counter', '0006_auto_20160717_1033'),
    ]

    operations = [
        migrations.CreateModel(
            name='Permanency',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('start', models.DateTimeField(verbose_name='start date')),
                ('end', models.DateTimeField(verbose_name='end date')),
                ('counter', models.ForeignKey(related_name='permanencies', to='counter.Counter')),
                ('user', models.ForeignKey(related_name='permanencies', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
