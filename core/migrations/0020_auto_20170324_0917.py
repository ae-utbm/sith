# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("core", "0019_preferences_receive_weekmail")]

    operations = [
        migrations.AlterModelOptions(name="group", options={"ordering": ["name"]}),
        migrations.AlterField(
            model_name="page",
            name="name",
            field=models.CharField(
                validators=[
                    django.core.validators.RegexValidator(
                        "^[A-z.+-]+$",
                        "Enter a valid page name. This value may contain only unaccented letters, numbers and ./+/-/_ characters.",
                    )
                ],
                max_length=30,
                verbose_name="page unix name",
            ),
        ),
    ]
