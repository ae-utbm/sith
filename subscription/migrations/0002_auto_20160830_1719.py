# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("subscription", "0001_initial")]

    operations = [
        migrations.AlterField(
            model_name="subscription",
            name="location",
            field=models.CharField(
                max_length=20,
                verbose_name="location",
                choices=[
                    ("BELFORT", "Belfort"),
                    ("SEVENANS", "Sevenans"),
                    ("MONTBELIARD", "Montbéliard"),
                    ("EBOUTIC", "Eboutic"),
                ],
            ),
        )
    ]
