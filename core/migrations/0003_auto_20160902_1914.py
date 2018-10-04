# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [("core", "0002_auto_20160831_0144")]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="username",
            field=models.CharField(
                error_messages={"unique": "A user with that username already exists."},
                max_length=254,
                unique=True,
                validators=[
                    django.core.validators.RegexValidator(
                        "^[\\w.+-]+$",
                        "Enter a valid username. This value may contain only letters, numbers and ./+/-/_ characters.",
                    )
                ],
                help_text="Required. 254 characters or fewer. Letters, digits and ./+/-/_ only.",
                verbose_name="username",
            ),
        )
    ]
