# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("trombi", "0002_trombi_show_profiles")]

    operations = [
        migrations.AddField(
            model_name="trombicomment",
            name="is_moderated",
            field=models.BooleanField(
                default=False, verbose_name="is the comment moderated"
            ),
        )
    ]
