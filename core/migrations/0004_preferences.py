# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_auto_20160705_2304'),
    ]

    operations = [
        migrations.CreateModel(
            name='Preferences',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('show_my_stats', models.BooleanField(verbose_name='define if we show a users stats', default=False, help_text='Show your account statistics to others')),
                ('user', models.OneToOneField(related_name='preferences', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
