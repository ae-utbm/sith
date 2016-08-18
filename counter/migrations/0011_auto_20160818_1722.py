# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('counter', '0010_auto_20160818_1716'),
    ]

    operations = [
        migrations.AlterField(
            model_name='selling',
            name='club',
            field=models.ForeignKey(related_name='sellings', null=True, on_delete=django.db.models.deletion.SET_NULL, to='club.Club'),
        ),
        migrations.AlterField(
            model_name='selling',
            name='counter',
            field=models.ForeignKey(related_name='sellings', null=True, on_delete=django.db.models.deletion.SET_NULL, to='counter.Counter'),
        ),
        migrations.AlterField(
            model_name='selling',
            name='customer',
            field=models.ForeignKey(related_name='buyings', null=True, on_delete=django.db.models.deletion.SET_NULL, to='counter.Customer'),
        ),
        migrations.AlterField(
            model_name='selling',
            name='product',
            field=models.ForeignKey(related_name='sellings', null=True, on_delete=django.db.models.deletion.SET_NULL, blank=True, to='counter.Product'),
        ),
        migrations.AlterField(
            model_name='selling',
            name='seller',
            field=models.ForeignKey(related_name='sellings_as_operator', null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
    ]
