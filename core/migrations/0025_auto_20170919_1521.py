# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [("core", "0024_auto_20170906_1317")]

    operations = [
        migrations.AlterField(
            model_name="page",
            name="name",
            field=models.CharField(
                max_length=30,
                verbose_name="page unix name",
                validators=[
                    django.core.validators.RegexValidator(
                        "^[a-zA-Z0-9][a-zA-Z0-9._-]*[a-zA-Z0-9]$",
                        "Enter a valid page name. This value may contain only unaccented letters, numbers and ./+/-/_ characters.",
                    )
                ],
            ),
        )
    ]
