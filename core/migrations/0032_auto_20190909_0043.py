# Generated by Django 1.11.24 on 2019-09-08 22:43
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("core", "0031_auto_20190906_1615")]

    operations = [
        migrations.AlterField(
            model_name="notification",
            name="viewed",
            field=models.BooleanField(
                db_index=True, default=False, verbose_name="viewed"
            ),
        )
    ]
