# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('club', '0009_mailing_mailingsubscription'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mailingsubscription',
            name='email',
            field=models.EmailField(verbose_name='Email address', max_length=254),
        ),
        migrations.AlterUniqueTogether(
            name='mailingsubscription',
            unique_together=set([('user', 'email', 'mailing')]),
        ),
    ]
